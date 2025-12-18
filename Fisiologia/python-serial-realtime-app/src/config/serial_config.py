"""
Configuración específica del puerto serie
"""
import serial
import serial.tools.list_ports

class SerialConfig:
    """Gestión de configuración del puerto serie"""
    
    @staticmethod
    def get_available_ports():
        """Obtiene lista de puertos serie disponibles"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    @staticmethod
    def validate_port(port, baud=115200):
        """Valida si un puerto serie es accesible"""
        try:
            ser = serial.Serial(port, baud, timeout=1)
            ser.close()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_default_port():
        """Obtiene el puerto por defecto según el sistema operativo"""
        import platform
        system = platform.system()
        
        if system == 'Linux':
            # Buscar puertos USB comunes en Linux
            common_ports = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyUSB1']
            for port in common_ports:
                if SerialConfig.validate_port(port):
                    return port
        elif system == 'Windows':
            # Buscar puertos COM en Windows
            for i in range(1, 20):
                port = f'COM{i}'
                if SerialConfig.validate_port(port):
                    return port
        elif system == 'Darwin':  # macOS
            # Buscar puertos USB en macOS
            available_ports = SerialConfig.get_available_ports()
            usb_ports = [p for p in available_ports if 'usb' in p.lower()]
            if usb_ports:
                return usb_ports[0]
        
        return None
