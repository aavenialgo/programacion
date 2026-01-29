"""
Configuración del servidor WebSocket para visualización de señales PPG en tiempo real.
"""
import os

# ============================================================================
# Configuración del Puerto Serial
# ============================================================================
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")  # Windows: "COM3", Linux: "/dev/ttyUSB0"
BAUD_RATE = int(os.getenv("BAUD_RATE", "115200"))
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "100"))  # Hz
SERIAL_TIMEOUT = 1.0  # segundos

# ============================================================================
# Configuración del Servidor WebSocket
# ============================================================================
WS_HOST = os.getenv("WS_HOST", "0.0.0.0")  # Accesible en red local
WS_PORT = int(os.getenv("WS_PORT", "8765"))
PASSWORD = os.getenv("WS_PASSWORD", "cambiar123")  # Cambiar en producción

# ============================================================================
# Configuración del Filtro Butterworth por Defecto
# ============================================================================
DEFAULT_FILTER_LOW = 0.5  # Hz
DEFAULT_FILTER_HIGH = 45.0  # Hz
DEFAULT_FILTER_ORDER = 4
FILTER_ENABLED = True  # Filtro activo por defecto

# ============================================================================
# Configuración de Visualización
# ============================================================================
DEFAULT_WINDOW_SECONDS = 10  # Ventana de visualización por defecto
MAX_CLIENTS = 4  # Máximo de clientes simultáneos
BUFFER_SIZE = 1000  # Tamaño del buffer de datos

# ============================================================================
# Configuración de Calidad
# ============================================================================
QUALITY_WINDOW_SECONDS = 60  # Ventana para estadísticas de calidad
QUALITY_UPDATE_INTERVAL = 1.0  # Segundos entre actualizaciones de calidad

# ============================================================================
# Modos de Operación
# ============================================================================
# Modo de lectura de datos:
# "serial" - Lee directamente del puerto serial
# "tkinter" - Recibe datos de la aplicación Tkinter
# "auto" - Intenta serial primero, luego tkinter si falla
DATA_SOURCE_MODE = os.getenv("DATA_SOURCE_MODE", "auto")

# ============================================================================
# Configuración de Logging
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR

# ============================================================================
# Configuración de Seguridad
# ============================================================================
# Tokens de sesión expiran después de N horas
SESSION_TIMEOUT_HOURS = 24

# ============================================================================
# Configuración de Archivos CSV
# ============================================================================
UPLOAD_DIR = "uploads"  # Directorio para archivos CSV subidos
MAX_UPLOAD_SIZE_MB = 50  # Tamaño máximo de archivo CSV
