"""
Constantes utilizadas en toda la aplicación
"""
import re

# === PATRONES REGEX ===
# Patrón para extraer datos del puerto serie
SERIAL_DATA_PATTERN = re.compile(
    r"Crudo:(-?\d+(?:\.\d+)?),Filtrado:(-?\d+(?:\.\d+)?),Normalizado:(-?\d+(?:\.\d+)?)", 
    re.IGNORECASE
)

# === CONSTANTES MATEMÁTICAS ===
PI = 3.14159265359

# === CÓDIGOS DE ERROR ===
class ErrorCodes:
    SUCCESS = 0
    SERIAL_CONNECTION_ERROR = 1001
    DATA_PROCESSING_ERROR = 1002
    FILE_IO_ERROR = 1003
    ANALYSIS_ERROR = 1004

# === ESTADOS DE LA APLICACIÓN ===
class AppStates:
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ACQUIRING = "acquiring"
    PAUSED = "paused"
    ANALYZING = "analyzing"

# === TIPOS DE SEÑAL ===
class SignalTypes:
    RAW = "raw"
    FILTERED = "filtered" 
    NORMALIZED = "normalized"

# === UNIDADES ===
class Units:
    TIME = "segundos"
    AMPLITUDE = "unidades"
    FREQUENCY = "Hz"
    HEART_RATE = "BPM"
