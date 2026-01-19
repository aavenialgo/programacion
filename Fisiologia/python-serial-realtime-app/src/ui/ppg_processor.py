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
        """Resetea todos los buffers de datos"""
        self.time_buffer.clear()
        self.raw_buffer.clear()
        self.filtered_buffer.clear()
        self.normalized_buffer.clear()
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
        
    def add_data_point(self, raw_value, filtered_value=None, normalized_value=None):
        """Agrega un nuevo punto de datos"""
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
        """Realiza el análisis periódico de la señal"""
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

    def calculate_derivatives(self, data):
        """Calcula la primera y segunda derivada usando diferencias centrales."""
        if len(data) < 3:
            return np.array([]), np.array([])

        dt = 1.0 / self.fs

        d1_dt = np.gradient(data, dt)
        d2_dt2 = np.gradient(d1_dt, dt)

        return d1_dt, d2_dt2

    def analyze_segment(self, t_segment, ppg_segment):
        """Analiza morfología en una ventana PPG y calcula puntos/parametros."""
        if len(ppg_segment) < 100:
            return None, {}

        try:
            ppg_smooth = savgol_filter(ppg_segment, window_length=int(self.fs / 5) + 1, polyorder=3)
        except Exception:
            ppg_smooth = ppg_segment

        d1, d2 = self.calculate_derivatives(ppg_smooth)
        t_aligned = t_segment

        peaks, _ = find_peaks(ppg_smooth, height=np.mean(ppg_smooth), distance=int(self.fs / 2))
        if not list(peaks):
            peaks, _ = find_peaks(ppg_smooth, distance=int(self.fs / 2))

        systolic_peak_idx = peaks

        dicrotic_notch_idx = []
        for p_idx in systolic_peak_idx:
            search_start = min(p_idx + int(self.fs * 0.1), len(ppg_smooth) - 1)
            search_end = min(p_idx + int(self.fs * 0.5), len(ppg_smooth))
            if search_start < search_end:
                valley_idx_local = np.argmin(ppg_smooth[search_start:search_end])
                dicrotic_notch_idx.append(search_start + valley_idx_local)

        d2_peaks, _ = find_peaks(d2, distance=int(self.fs / 4))
        d2_valleys, _ = find_peaks(-d2, distance=int(self.fs / 4))

        fiducial_points = {
            'systolic_peak': t_aligned[systolic_peak_idx],
            'dicrotic_notch': t_aligned[dicrotic_notch_idx],
            'd2_a': t_aligned[d2_peaks[0]] if len(d2_peaks) > 0 else None,
            'd2_b': t_aligned[d2_valleys[0]] if len(d2_valleys) > 0 else None,
            'd2_c': t_aligned[d2_peaks[1]] if len(d2_peaks) > 1 else None,
            'd2_d': t_aligned[d2_valleys[1]] if len(d2_valleys) > 1 else None,
            'd2_e': t_aligned[d2_peaks[2]] if len(d2_peaks) > 2 else None,
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
        dc = np.mean(ppg_segment)

        rt = np.nan
        st_dt_ratio = np.nan

        if len(systolic_peak_idx) > 0 and len(dicrotic_notch_idx) > 0:
            pico_idx = systolic_peak_idx[0]
            valle_idx = np.argmin(ppg_segment[:pico_idx])
            notch_idx = dicrotic_notch_idx[0]

            rt = (t_aligned[pico_idx] - t_aligned[valle_idx]) if valle_idx < pico_idx else np.nan

            systolic_time = t_aligned[notch_idx] - t_aligned[pico_idx]
            diastolic_time = (t_aligned[-1] - t_aligned[notch_idx]) if len(t_aligned) > 1 else np.nan

            if not np.isnan(systolic_time) and not np.isnan(diastolic_time) and diastolic_time > 0:
                st_dt_ratio = systolic_time / diastolic_time

        a = ppg_smooth[d2_peaks[0]] if len(d2_peaks) > 0 else np.nan
        b = ppg_smooth[d2_valleys[0]] if len(d2_valleys) > 0 else np.nan
        c = ppg_smooth[d2_peaks[1]] if len(d2_peaks) > 1 else np.nan
        d = ppg_smooth[d2_valleys[1]] if len(d2_valleys) > 1 else np.nan
        e = ppg_smooth[d2_peaks[2]] if len(d2_peaks) > 2 else np.nan

        ai = np.nan
        if len(dicrotic_notch_idx) > 0:
            ai = ppg_smooth[dicrotic_notch_idx[0]] / ppg_smooth[systolic_peak_idx[0]]

        parameters = {
            'FC (LPM)': f'{fc:.2f}' if not np.isnan(fc) else 'N/A',
            'PPI (s)': f'{avg_ppi:.3f}' if not np.isnan(avg_ppi) else 'N/A',
            'AC (Unidades)': f'{ac:.2f}',
            'DC (Unidades)': f'{dc:.2f}',
            'AI (Proxy)': f'{ai:.3f}' if not np.isnan(ai) else 'N/A',
            'RT (ms)': f'{rt * 1000:.1f}' if not np.isnan(rt) else 'N/A',
            'ST/DT': f'{st_dt_ratio:.2f}' if not np.isnan(st_dt_ratio) else 'N/A',
            'Ratio b/a': f'{(b/a):.2f}' if not np.isnan(a) and not np.isnan(b) and a != 0 else 'N/A',
            'Ratio c/a': f'{(c/a):.2f}' if not np.isnan(a) and not np.isnan(c) and a != 0 else 'N/A',
            'Ratio d/a': f'{(d/a):.2f}' if not np.isnan(a) and not np.isnan(d) and a != 0 else 'N/A',
            'Ratio e/a': f'{(e/a):.2f}' if not np.isnan(a) and not np.isnan(e) and a != 0 else 'N/A',
        }

        analysis_data = {
            'time': t_aligned,
            'ppg': ppg_segment,
            'ppg_smooth': ppg_smooth,
            'd1': d1,
            'd2': d2,
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
        """Obtiene los datos para mostrar en un gráfico

        Returns:
            _type_: _description_
        """
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
        """Obtiene las estadísticas actuales"""
        return {
            'heart_rate': self.current_hr,
            'hrv': self.current_hrv,
            'data_points': len(self.time_buffer),
            'duration': self.time_buffer[-1] if self.time_buffer else 0
        }
