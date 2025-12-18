"""
Módulo para el procesamiento de señales PPG en tiempo real
"""
from collections import deque
import numpy as np
import time
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from scipy.signal import find_peaks

class PPGProcessor(QObject):
    """Procesador de señales PPG con análisis en tiempo real"""
    
    # Señales para comunicación con la UI
    new_data_processed = pyqtSignal()
    analysis_complete = pyqtSignal(dict)
    segment_analyzed = pyqtSignal(dict)
    buffer_full = pyqtSignal()
    
    def __init__(self, sample_rate=125, buffer_size=7500):  # 60 segundos @ 125Hz
        super().__init__()
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # Buffers de datos
        self.time_buffer = deque(maxlen=buffer_size)
        self.raw_buffer = deque(maxlen=buffer_size)
        self.filtered_buffer = deque(maxlen=buffer_size)
        self.normalized_buffer = deque(maxlen=buffer_size)
        
        # Variables de estado
        self.start_time = None
        self.last_analysis_time = 0
        self.analysis_interval = 5.0  # Analizar cada 5 segundos
        
        # Timer para análisis periódico
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self._periodic_analysis)
        
        # Estadísticas en tiempo real
        self.current_hr = 0
        self.current_hrv = 0
        
    def reset_data(self):
        """Resetear todos los buffers de datos"""
        self.time_buffer.clear()
        self.raw_buffer.clear()
        self.filtered_buffer.clear()
        self.normalized_buffer.clear()
        self.start_time = None
        self.last_analysis_time = 0
        self.current_hr = 0
        self.current_hrv = 0
        
    def start_processing(self):
        """Iniciar el procesamiento de datos"""
        self.analysis_timer.start(int(self.analysis_interval * 1000))
        
    def stop_processing(self):
        """Detener el procesamiento de datos"""
        self.analysis_timer.stop()
        
    def add_data_point(self, raw_value, filtered_value=None, normalized_value=None):
        """Agregar un nuevo punto de datos"""
        try:
            current_time = time.time()
            
            if self.start_time is None:
                self.start_time = current_time
                
            relative_time = current_time - self.start_time
            
            # Agregar a buffers
            self.time_buffer.append(relative_time)
            self.raw_buffer.append(raw_value)
            self.filtered_buffer.append(filtered_value if filtered_value is not None else raw_value)
            self.normalized_buffer.append(normalized_value if normalized_value is not None else raw_value)
            
            self.new_data_processed.emit()
            
            # Verificar si el buffer está lleno
            if len(self.time_buffer) >= self.buffer_size:
                self.buffer_full.emit()
                
        except Exception as e:
            print(f"Error procesando datos: {e}")
            
    def _periodic_analysis(self):
        """Realizar análisis periódico de la señal"""
        if len(self.filtered_buffer) < self.sample_rate * 2:  # Necesitamos al menos 2 segundos
            return
            
        try:
            # Obtener los últimos 5 segundos de datos
            segment_size = min(self.sample_rate * 5, len(self.filtered_buffer))
            signal_segment = list(self.filtered_buffer)[-segment_size:]
            time_segment = list(self.time_buffer)[-segment_size:]
            
            if len(signal_segment) > 0:
                # Realizar análisis
                results = self._analyze_segment(signal_segment, time_segment)
                if results:
                    self.current_hr = results.get('heart_rate', 0)
                    self.current_hrv = results.get('hrv', 0)
                    self.analysis_complete.emit(results)
                
        except Exception as e:
            print(f"Error en análisis periódico: {e}")
            
    def _analyze_segment(self, signal, time_data):
        """Analizar un segmento de señal PPG"""
        try:
            if len(signal) < 100:
                return None
                
            # Convertir a arrays numpy
            signal = np.array(signal)
            time_data = np.array(time_data)
            
            # Normalizar señal
            signal_norm = (signal - np.mean(signal)) / np.std(signal)
            
            # Detectar picos
            # Distancia mínima entre picos: ~0.4s (150 BPM máximo)
            min_distance = int(0.4 * self.sample_rate)
            peaks, properties = find_peaks(signal_norm, 
                                         height=0.3,  # Altura mínima
                                         distance=min_distance)
            
            results = {
                'num_peaks': len(peaks),
                'heart_rate': 0,
                'hrv': 0,
                'signal_quality': 'good'
            }
            
            if len(peaks) >= 2:
                # Calcular intervalos RR (en segundos)
                rr_intervals = np.diff(time_data[peaks])
                
                # Calcular frecuencia cardíaca
                mean_rr = np.mean(rr_intervals)
                heart_rate = 60.0 / mean_rr if mean_rr > 0 else 0
                
                # Calcular HRV (RMSSD)
                if len(rr_intervals) > 1:
                    rr_diff = np.diff(rr_intervals)
                    hrv = np.sqrt(np.mean(rr_diff**2)) * 1000  # en ms
                else:
                    hrv = 0
                
                results.update({
                    'heart_rate': heart_rate,
                    'hrv': hrv,
                    'rr_intervals': rr_intervals.tolist(),
                    'peak_times': time_data[peaks].tolist(),
                    'mean_rr': mean_rr
                })
                
                # Evaluar calidad de la señal
                if heart_rate < 40 or heart_rate > 200:
                    results['signal_quality'] = 'poor'
                elif len(peaks) < 3:
                    results['signal_quality'] = 'fair'
                    
            return results
            
        except Exception as e:
            print(f"Error analizando segmento: {e}")
            return None
            
    def analyze_custom_segment(self, start_time, end_time):
        """Analizar un segmento específico de la señal"""
        try:
            # Encontrar índices para el segmento
            time_array = np.array(self.time_buffer)
            start_idx = np.searchsorted(time_array, start_time)
            end_idx = np.searchsorted(time_array, end_time)
            
            if start_idx >= end_idx or end_idx > len(self.filtered_buffer):
                return None
                
            # Extraer segmento
            signal_segment = list(self.filtered_buffer)[start_idx:end_idx]
            time_segment = list(self.time_buffer)[start_idx:end_idx]
            
            if len(signal_segment) > 100:  # Mínimo de datos requerido
                results = self._analyze_segment(signal_segment, time_segment)
                if results:
                    self.segment_analyzed.emit(results)
                return results
                
        except Exception as e:
            print(f"Error analizando segmento personalizado: {e}")
            return None
            
    def get_display_data(self, max_points=2500):
        """Obtener datos para mostrar en gráficos"""
        if not self.time_buffer:
            return [], [], [], []
            
        # Limitar el número de puntos para mejor rendimiento
        if len(self.time_buffer) <= max_points:
            return (list(self.time_buffer), 
                   list(self.raw_buffer), 
                   list(self.filtered_buffer),
                   list(self.normalized_buffer))
        else:
            # Tomar los últimos max_points puntos
            return (list(self.time_buffer)[-max_points:],
                   list(self.raw_buffer)[-max_points:],
                   list(self.filtered_buffer)[-max_points:],
                   list(self.normalized_buffer)[-max_points:])
                   
    def get_current_stats(self):
        """Obtener estadísticas actuales"""
        return {
            'heart_rate': self.current_hr,
            'hrv': self.current_hrv,
            'data_points': len(self.time_buffer),
            'duration': self.time_buffer[-1] if self.time_buffer else 0
        }
