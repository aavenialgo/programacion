"""
Módulo para la lectura de datos del puerto serie en un hilo separado
"""
import threading
import time
import re
from PyQt5.QtCore import QObject, pyqtSignal

class SerialReader(QObject):
    """Clase para leer datos del puerto serie en un hilo separado"""
    
    # Señales para comunicación con la UI
    data_received = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.reading = False
        self.reading_thread = None
        
        # Regex para extraer los valores del formato esperado
        self.pattern = re.compile(
            r"Crudo:(-?\d+(?:\.\d+)?),Filtrado:(-?\d+(?:\.\d+)?),Normalizado:(-?\d+(?:\.\d+)?)", 
            re.IGNORECASE
        )
        
    def start_reading(self, serial_port):
        """Iniciar la lectura del puerto serie"""
        if self.reading:
            return
            
        self.serial_port = serial_port
        self.reading = True
        self.reading_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.reading_thread.start()
        self.connection_status_changed.emit(True)
        
    def stop_reading(self):
        """Detener la lectura del puerto serie"""
        self.reading = False
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join(timeout=1.0)
        self.connection_status_changed.emit(False)
        
    def _read_loop(self):
        """Bucle principal de lectura de datos"""
        while self.reading and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line:
                        # Emitir la línea completa para procesamiento posterior
                        self.data_received.emit(line)
                else:
                    time.sleep(0.001)  # Pequeña pausa para no saturar CPU
            except Exception as e:
                self.error_occurred.emit(str(e))
                self.reading = False
                break
                
    def is_reading(self):
        """Verificar si está leyendo datos"""
        return self.reading
        
    def parse_data_line(self, line):
        """Parsear línea de datos y extraer valores"""
        try:
            match = self.pattern.search(line)
            if match:
                raw = float(match.group(1))
                filtered = float(match.group(2))
                normalized = float(match.group(3))
                return raw, filtered, normalized
        except (ValueError, AttributeError):
            pass
        return None
