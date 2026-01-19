"""
Configuraciones generales. Incluye parametros del puerto serie, configuraciones de señal,
filtros, análisis, interfaz y exportación de datos.
"""

# === CONFIGURACIONES DEL PUERTO SERIE ===
DEFAULT_PORT = '/dev/ttyUSB0'
DEFAULT_BAUD = 115200
TIMEOUT = 1

# === CONFIGURACIONES DE SEÑAL ===
SAMPLING_FREQUENCY = 125  # Hz
MAX_POINTS = SAMPLING_FREQUENCY * 60  # Buffer de 60 segundos
DEFAULT_WINDOW_SIZE = 5  # segundos para visualización

# === CONFIGURACIONES DE FILTROS ===
# Filtro pasa banda
LOWCUT = 0.5  # Hz
HIGHCUT = 8.0  # Hz
FILTER_ORDER = 4

# Filtro de media móvil
DEFAULT_MOVING_AVERAGE_WINDOW = 5

# === CONFIGURACIONES DE ANÁLISIS ===
# Para detección de picos
MIN_PEAK_HEIGHT = 0.1
MIN_PEAK_DISTANCE = int(SAMPLING_FREQUENCY * 0.4)  # 400ms mínimo entre picos

# Para análisis de segmentos
DEFAULT_SEGMENT_DURATION = 10  # segundos
OVERLAP_PERCENTAGE = 50  # % de solapamiento entre segmentos

# === CONFIGURACIONES DE INTERFAZ ===
# Tamaños de ventana
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800

# Colores de la interfaz
COLORS = {
    'raw': '#FF6B6B',      # Rojo para señal cruda
    'filtered': '#4ECDC4',  # Turquesa para señal filtrada
    'normalized': '#45B7D1', # Azul para señal normalizada
    'peaks': '#FFA07A',     # Naranja para picos
    'background': '#FFFFFF', # Fondo blanco
    'foreground': '#333333', # Texto gris oscuro
}

# === CONFIGURACIONES DE EXPORTACIÓN ===
DEFAULT_EXPORT_FORMAT = 'csv'
EXPORT_FORMATS = ['csv', 'xlsx', 'json']

# Columnas para exportación
EXPORT_COLUMNS = [
    'timestamp',
    'raw_signal',
    'filtered_signal', 
    'normalized_signal'
]
