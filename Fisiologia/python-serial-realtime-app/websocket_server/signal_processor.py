"""
Procesamiento de señales con filtros Butterworth usando scipy.
"""
import numpy as np
from scipy.signal import butter, lfilter, filtfilt
from collections import deque
import logging

logger = logging.getLogger(__name__)


class SignalProcessor:
    """
    Procesador de señales con filtro Butterworth pasa banda.
    
    Mantiene un buffer de datos y aplica filtros digitales en tiempo real.
    """
    
    def __init__(self, sample_rate=100, buffer_size=1000):
        """
        Inicializa el procesador de señales.
        
        Args:
            sample_rate: Frecuencia de muestreo en Hz
            buffer_size: Tamaño máximo del buffer de datos
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # Buffers para datos crudos y filtrados
        self.raw_buffer = deque(maxlen=buffer_size)
        self.filtered_buffer = deque(maxlen=buffer_size)
        self.time_buffer = deque(maxlen=buffer_size)
        
        # Configuración del filtro
        self.filter_enabled = True
        self.lowcut = 0.5
        self.highcut = 45.0
        self.order = 4
        
        # Coeficientes del filtro
        self._update_filter_coefficients()
        
        # Estado del filtro para lfilter (procesamiento en tiempo real)
        self.zi = None
        
    def _update_filter_coefficients(self):
        """Actualiza los coeficientes del filtro Butterworth."""
        try:
            nyq = 0.5 * self.sample_rate
            low = self.lowcut / nyq
            high = self.highcut / nyq
            
            # Validaciones
            if low <= 0 or low >= 1:
                raise ValueError(f"Frecuencia de corte baja fuera de rango: {self.lowcut} Hz")
            if high <= 0 or high >= 1:
                raise ValueError(f"Frecuencia de corte alta fuera de rango: {self.highcut} Hz")
            if low >= high:
                raise ValueError("Frecuencia baja debe ser menor que frecuencia alta")
            
            self.b, self.a = butter(self.order, [low, high], btype='band')
            
            # Reiniciar estado del filtro
            self.zi = None
            
            logger.info(
                f"Filtro actualizado: {self.lowcut}-{self.highcut} Hz, orden {self.order}"
            )
            
        except Exception as e:
            logger.error(f"Error actualizando coeficientes del filtro: {e}")
            # Mantener coeficientes anteriores
            
    def configure_filter(self, lowcut=None, highcut=None, order=None, enabled=None):
        """
        Configura los parámetros del filtro.
        
        Args:
            lowcut: Frecuencia de corte baja en Hz
            highcut: Frecuencia de corte alta en Hz
            order: Orden del filtro
            enabled: Activar/desactivar filtro
            
        Returns:
            dict: Configuración actual del filtro
        """
        if lowcut is not None:
            self.lowcut = lowcut
        if highcut is not None:
            self.highcut = highcut
        if order is not None:
            self.order = order
        if enabled is not None:
            self.filter_enabled = enabled
            
        self._update_filter_coefficients()
        
        return self.get_filter_config()
    
    def get_filter_config(self):
        """Retorna la configuración actual del filtro."""
        return {
            "enabled": self.filter_enabled,
            "lowcut": self.lowcut,
            "highcut": self.highcut,
            "order": self.order,
            "sample_rate": self.sample_rate
        }
    
    def process_sample(self, timestamp, raw_value):
        """
        Procesa una nueva muestra de datos.
        
        Args:
            timestamp: Tiempo relativo en segundos
            raw_value: Valor crudo de la señal
            
        Returns:
            tuple: (timestamp, raw_value, filtered_value)
        """
        # Agregar a buffers
        self.time_buffer.append(timestamp)
        self.raw_buffer.append(raw_value)
        
        # Aplicar filtro si está habilitado
        if self.filter_enabled and len(self.raw_buffer) > self.order * 3:
            try:
                # Usar lfilter para procesamiento en tiempo real
                if self.zi is None:
                    # Inicializar estado del filtro
                    self.zi = np.zeros(max(len(self.b), len(self.a)) - 1)
                
                # Filtrar la nueva muestra
                filtered_value, self.zi = lfilter(
                    self.b, self.a, [raw_value], zi=self.zi
                )
                filtered_value = filtered_value[0]
                
            except Exception as e:
                logger.warning(f"Error aplicando filtro: {e}")
                filtered_value = raw_value
        else:
            filtered_value = raw_value
        
        self.filtered_buffer.append(filtered_value)
        
        return timestamp, raw_value, filtered_value
    
    def apply_filter_to_array(self, data):
        """
        Aplica el filtro a un array completo de datos (para análisis offline).
        
        Args:
            data: Array de datos crudos
            
        Returns:
            np.ndarray: Datos filtrados
        """
        if not self.filter_enabled:
            return data
        
        try:
            if len(data) < self.order * 3:
                logger.warning("No hay suficientes datos para filtrar")
                return data
            
            # Usar filtfilt para filtrado offline (fase cero)
            filtered = filtfilt(self.b, self.a, data)
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtrando array: {e}")
            return data
    
    def get_buffer_data(self, window_seconds=None):
        """
        Retorna los datos en buffer.
        
        Args:
            window_seconds: Si se especifica, retorna solo los últimos N segundos
            
        Returns:
            dict: Diccionario con arrays de tiempo, datos crudos y filtrados
        """
        if len(self.time_buffer) == 0:
            return {
                "time": [],
                "raw": [],
                "filtered": []
            }
        
        time_array = np.array(self.time_buffer)
        raw_array = np.array(self.raw_buffer)
        filtered_array = np.array(self.filtered_buffer)
        
        if window_seconds is not None:
            # Filtrar solo los últimos window_seconds
            current_time = time_array[-1]
            mask = time_array >= (current_time - window_seconds)
            time_array = time_array[mask]
            raw_array = raw_array[mask]
            filtered_array = filtered_array[mask]
        
        return {
            "time": time_array.tolist(),
            "raw": raw_array.tolist(),
            "filtered": filtered_array.tolist()
        }
    
    def clear_buffer(self):
        """Limpia todos los buffers."""
        self.raw_buffer.clear()
        self.filtered_buffer.clear()
        self.time_buffer.clear()
        self.zi = None
        logger.info("Buffers limpiados")
    
    def get_buffer_size(self):
        """Retorna el tamaño actual del buffer."""
        return len(self.raw_buffer)


if __name__ == "__main__":
    # Ejemplo de uso
    import matplotlib.pyplot as plt
    
    # Crear procesador
    processor = SignalProcessor(sample_rate=100)
    
    # Configurar filtro
    processor.configure_filter(lowcut=0.5, highcut=10.0, order=4)
    
    # Generar señal de prueba (seno + ruido)
    t = np.linspace(0, 10, 1000)
    signal = np.sin(2 * np.pi * 2 * t) + 0.5 * np.sin(2 * np.pi * 25 * t) + 0.3 * np.random.randn(1000)
    
    # Procesar muestras
    for i, (time, value) in enumerate(zip(t, signal)):
        processor.process_sample(time, value)
    
    # Obtener datos
    data = processor.get_buffer_data()
    
    # Graficar
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(data['time'], data['raw'], label='Raw', alpha=0.7)
    plt.title('Señal Cruda')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('Amplitud')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    plt.plot(data['time'], data['filtered'], label='Filtered', color='orange')
    plt.title('Señal Filtrada')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('Amplitud')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
