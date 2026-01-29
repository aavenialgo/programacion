"""
Lector de puerto serial para captura de datos PPG en tiempo real.
"""
import serial
import serial.tools.list_ports
import asyncio
import logging
import re
from typing import Optional, Callable
import time

logger = logging.getLogger(__name__)


class SerialReader:
    """
    Lector asíncrono de puerto serial.
    
    Soporta múltiples formatos de datos:
    - "tiempo,valor" (formato simple)
    - "Crudo:X,Filtrado:Y,Normalizado:Z" (formato legacy)
    - Valores numéricos simples
    """
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        """
        Inicializa el lector serial.
        
        Args:
            port: Puerto serial (ej: "COM3" o "/dev/ttyUSB0")
            baudrate: Velocidad de transmisión
            timeout: Timeout de lectura en segundos
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_running = False
        self.callback: Optional[Callable] = None
        
        # Patrones regex para parsear diferentes formatos
        self.pattern_csv = re.compile(r'^([\d.]+),([-\d.]+)$')
        self.pattern_legacy = re.compile(
            r'Crudo:([-\d.]+),Filtrado:([-\d.]+),Normalizado:([-\d.]+)',
            re.IGNORECASE
        )
        self.pattern_simple = re.compile(r'^([-\d.]+)$')
        
        # Estadísticas
        self.samples_read = 0
        self.errors_count = 0
        self.start_time = None
        
    def connect(self) -> bool:
        """
        Abre la conexión al puerto serial.
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            if self.serial_conn and self.serial_conn.is_open:
                logger.info(f"Puerto {self.port} ya está abierto")
                return True
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            logger.info(
                f"Conectado a {self.port} @ {self.baudrate} baud"
            )
            return True
            
        except serial.SerialException as e:
            logger.error(f"Error abriendo puerto serial {self.port}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado conectando al serial: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión serial."""
        self.is_running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info(f"Desconectado de {self.port}")
    
    def parse_line(self, line: str) -> Optional[tuple]:
        """
        Parsea una línea de datos del serial.
        
        Args:
            line: Línea de texto recibida
            
        Returns:
            tuple: (timestamp, value) o None si no se pudo parsear
        """
        line = line.strip()
        if not line:
            return None
        
        try:
            # Formato: "tiempo,valor"
            match = self.pattern_csv.match(line)
            if match:
                timestamp = float(match.group(1))
                value = float(match.group(2))
                return (timestamp, value)
            
            # Formato legacy: "Crudo:X,Filtrado:Y,Normalizado:Z"
            match = self.pattern_legacy.search(line)
            if match:
                # Usar solo el valor crudo
                value = float(match.group(1))
                # Generar timestamp relativo
                if self.start_time is None:
                    self.start_time = time.time()
                timestamp = time.time() - self.start_time
                return (timestamp, value)
            
            # Formato simple: solo un número
            match = self.pattern_simple.match(line)
            if match:
                value = float(match.group(1))
                if self.start_time is None:
                    self.start_time = time.time()
                timestamp = time.time() - self.start_time
                return (timestamp, value)
            
            logger.debug(f"Línea no reconocida: {line}")
            return None
            
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parseando línea '{line}': {e}")
            return None
    
    async def read_loop(self, callback: Callable):
        """
        Bucle principal de lectura asíncrona.
        
        Args:
            callback: Función a llamar con cada dato: callback(timestamp, value)
        """
        self.callback = callback
        self.is_running = True
        self.start_time = time.time()
        
        logger.info("Iniciando bucle de lectura serial")
        
        while self.is_running:
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    logger.warning("Puerto serial no disponible")
                    await asyncio.sleep(1.0)
                    continue
                
                # Leer datos disponibles
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore')
                    
                    # Parsear línea
                    result = self.parse_line(line)
                    if result:
                        timestamp, value = result
                        self.samples_read += 1
                        
                        # Llamar callback
                        if self.callback:
                            await self.callback(timestamp, value)
                else:
                    # No hay datos, esperar un poco
                    await asyncio.sleep(0.001)
                    
            except serial.SerialException as e:
                logger.error(f"Error de serial: {e}")
                self.errors_count += 1
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Error en bucle de lectura: {e}")
                self.errors_count += 1
                await asyncio.sleep(0.1)
        
        logger.info("Bucle de lectura finalizado")
    
    def get_stats(self) -> dict:
        """Retorna estadísticas de lectura."""
        uptime = 0
        if self.start_time:
            uptime = time.time() - self.start_time
        
        return {
            "samples_read": self.samples_read,
            "errors_count": self.errors_count,
            "uptime_seconds": uptime,
            "is_running": self.is_running,
            "port": self.port,
            "baudrate": self.baudrate
        }
    
    @staticmethod
    def list_ports():
        """
        Lista todos los puertos seriales disponibles.
        
        Returns:
            list: Lista de puertos disponibles
        """
        ports = serial.tools.list_ports.comports()
        return [
            {
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid
            }
            for port in ports
        ]


async def test_serial_reader():
    """Función de prueba del lector serial."""
    
    # Listar puertos disponibles
    print("Puertos disponibles:")
    for port in SerialReader.list_ports():
        print(f"  - {port['device']}: {port['description']}")
    
    # Crear lector (ajustar puerto según disponibilidad)
    reader = SerialReader(port="COM3", baudrate=115200)
    
    # Callback de ejemplo
    async def on_data(timestamp, value):
        print(f"[{timestamp:.3f}s] Valor: {value}")
    
    # Conectar
    if reader.connect():
        try:
            # Leer por 10 segundos
            await asyncio.wait_for(reader.read_loop(on_data), timeout=10.0)
        except asyncio.TimeoutError:
            print("Tiempo de prueba finalizado")
        finally:
            reader.disconnect()
            
            # Mostrar estadísticas
            stats = reader.get_stats()
            print(f"\nEstadísticas:")
            print(f"  Muestras leídas: {stats['samples_read']}")
            print(f"  Errores: {stats['errors_count']}")
            print(f"  Tiempo activo: {stats['uptime_seconds']:.2f}s")
    else:
        print("No se pudo conectar al puerto serial")


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar prueba
    asyncio.run(test_serial_reader())
