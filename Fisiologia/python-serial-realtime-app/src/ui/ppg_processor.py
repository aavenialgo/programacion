"""
Módulo para el procesamiento de señales PPG en tiempo real
"""
from collections import deque
import numpy as np
import time
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from scipy.signal import find_peaks, savgol_filter

class PPGProcessor(QObject):
    """Procesador de señales PPG con análisis en tiempo real"""
    
    # Señales para comunicación con la UI 
    
    #: nueva señal procesada
    new_data_processed = pyqtSignal()
    #: contenedor del análisis completo
    analysis_complete = pyqtSignal(dict)
    #: segmento analizado
    segment_analyzed = pyqtSignal(dict)
    #: buffer de datos
    buffer_full = pyqtSignal()
    
    def __init__(self, sample_rate=100, buffer_size=7500):  # 60 segundos @ 100Hz
        super().__init__()
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.fs = sample_rate
        
        # Buffers de datos (solo canal raw)
        self.time_buffer = deque(maxlen=buffer_size)
        self.raw_buffer = deque(maxlen=buffer_size)
        
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
        """Resetea todos los buffers de datos"""
        self.time_buffer.clear()
        self.raw_buffer.clear()
        self.start_time = None
        self.last_analysis_time = 0
        self.current_hr = 0
        self.current_hrv = 0
        
    def start_processing(self):
        """Funcion del timer que inicia el procesamiento de datos"""
        self.analysis_timer.start(int(self.analysis_interval * 1000))
        
    def stop_processing(self):
        """funcion del timer que detiene el procesamiento de datos"""
        self.analysis_timer.stop()
        
    def add_data_point(self, raw_value):
        """Agrega un nuevo punto de datos del canal raw"""
        try:
            current_time = time.time()
            
            if self.start_time is None:
                self.start_time = current_time
                
            relative_time = current_time - self.start_time
            
            # Agregar a buffers
            self.time_buffer.append(relative_time)
            self.raw_buffer.append(raw_value)
            
            self.new_data_processed.emit()
            
            # Verificar si el buffer está lleno
            if len(self.time_buffer) >= self.buffer_size:
                self.buffer_full.emit()
                
        except Exception as e:
            print(f"Error procesando datos: {e}")
            
    def _periodic_analysis(self):
        """Realiza el análisis periódico de la señal"""
        if len(self.raw_buffer) < self.sample_rate * 2:  # Necesitamos al menos 2 segundos
            return
            
        try:
            # Obtener los últimos 5 segundos de datos
            segment_size = min(self.sample_rate * 5, len(self.raw_buffer))
            signal_segment = list(self.raw_buffer)[-segment_size:]
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
        """Analiza un segmento de señal PPG
        Se obtiene parámetros como fc, hrv y calidad de señal
        """
        try:
            if len(signal) < 100:
                return None
                
            # Convertir a arrays numpy
            signal = np.array(signal)
            time_data = np.array(time_data)
            
            # Normalizar señal
            signal_norm = (signal - np.mean(signal)) / np.std(signal)
            
            # Detectar picos
            # Distancia mínima entre picos: ~0.4s (150 BPM maximo)
            min_distance = int(0.4 * self.sample_rate)
            peaks, properties = find_peaks(signal_norm, 
                                         height=0.3,  # Altura minima
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

    def calculate_derivative(self, data):
        """Calcula la primera derivada usando diferencias centrales."""
        if len(data) < 3:
            return np.array([])

        dt = 1.0 / self.fs
        d1_dt = np.gradient(data, dt)
        return d1_dt

    def calculate_derivatives(self, data):
        """Compatibilidad retroactiva: retorna d1 y un arreglo vacío para d2."""
        d1_dt = self.calculate_derivative(data)
        return d1_dt, np.array([])

    def analyze_segment(self, t_segment, ppg_segment):
        """Analiza morfología en una ventana PPG y calcula puntos/parametros."""
        if len(ppg_segment) < 100:
            return None, {}

        t_aligned = np.asarray(t_segment)
        ppg_segment = np.asarray(ppg_segment)

        try:
            ppg_smooth = savgol_filter(ppg_segment, window_length=int(self.fs / 5) + 1, polyorder=3)
        except Exception:
            ppg_smooth = ppg_segment

        d1 = self.calculate_derivative(ppg_smooth)

        peaks, _ = find_peaks(ppg_smooth, height=np.mean(ppg_smooth), distance=int(self.fs / 2))
        if not list(peaks):
            peaks, _ = find_peaks(ppg_smooth, distance=int(self.fs / 2))

        systolic_peak_idx = peaks

        foot_idx = []
        for p_idx in systolic_peak_idx:
            foot_start = max(p_idx - int(self.fs * 0.5), 0)
            foot_end = p_idx
            if foot_start < foot_end:
                valley_before_peak = np.argmin(ppg_smooth[foot_start:foot_end])
                foot_idx.append(foot_start + valley_before_peak)

        fiducial_points = {
            'systolic_peak': t_aligned[systolic_peak_idx],
            'foot': t_aligned[foot_idx],
        }

        if len(systolic_peak_idx) > 1:
            ppi_samples = np.diff(systolic_peak_idx)
            ppi_seconds = ppi_samples / self.fs
            avg_ppi = np.mean(ppi_seconds)
            fc = 60 / avg_ppi
        else:
            fc = np.nan
            avg_ppi = np.nan

        ac = np.max(ppg_segment) - np.min(ppg_segment)
        parameters = {
            'FC (LPM)': f'{fc:.2f}' if not np.isnan(fc) else 'N/A',
            'PPI (s)': f'{avg_ppi:.3f}' if not np.isnan(avg_ppi) else 'N/A',
            'AC (Unidades)': f'{ac:.2f}',
        }

        analysis_data = {
            'time': t_aligned,
            'ppg': ppg_segment,
            'ppg_smooth': ppg_smooth,
            'd1': d1,
            'fiducials': fiducial_points,
            'parameters': parameters
        }

        return analysis_data, parameters
            
    def analyze_custom_segment(self, start_time, end_time):
        """Analiza un segmento específico de la señal"""
        try:
            # Encontrar índices para el segmento
            time_array = np.array(self.time_buffer)
            start_idx = np.searchsorted(time_array, start_time)
            end_idx = np.searchsorted(time_array, end_time)
            
            if start_idx >= end_idx or end_idx > len(self.raw_buffer):
                return None
                
            # Extraer segmento
            signal_segment = list(self.raw_buffer)[start_idx:end_idx]
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
        """Obtiene los datos para mostrar en un gráfico

        Returns:
            tuple: (time_data, raw_data) - Listas de tiempos y valores raw
        """
        if not self.time_buffer:
            return [], []
            
        # Limitar el número de puntos para mejor rendimiento
        if len(self.time_buffer) <= max_points:
            return (list(self.time_buffer), 
                   list(self.raw_buffer))
        else:
            # Tomar los últimos max_points puntos
            return (list(self.time_buffer)[-max_points:],
                   list(self.raw_buffer)[-max_points:])
                   
    def get_current_stats(self):
        """Obtiene las estadísticas actuales"""
        return {
            'heart_rate': self.current_hr,
            'hrv': self.current_hrv,
            'data_points': len(self.time_buffer),
            'duration': self.time_buffer[-1] if self.time_buffer else 0
        }
