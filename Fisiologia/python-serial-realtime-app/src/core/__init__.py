"""
Módulo core - Funciones principales de procesamiento y análisis de señales PPG.

Este módulo contiene:
- Análisis de señales PPG (ppg_analisis.py)
- Filtrado de señales (filter.py)
- Procesamiento en tiempo real (ppg_processor.py)
- Manejo de comunicación serial (serial_handler.py)
"""

# Importar funciones de análisis PPG
from .ppg_analisis import (
    get_temporal_features,
    get_dc_component,
    get_ac_component
)

# Importar funciones de filtrado
from .filter import (
    apply_filter,
    linebase_removal
)

# Importar clases principales
try:
    from .ppg_processor import PPGProcessor
except ImportError as e:
    print(f"Warning: No se pudo importar PPGProcessor: {e}")

try:
    from .serial_handler import SerialHandler
except ImportError as e:
    print(f"Warning: No se pudo importar SerialHandler: {e}")

__all__ = [
    # Análisis PPG
    'get_temporal_features',
    'get_dc_component', 
    'get_ac_component',
    # Filtrado
    'apply_filter',
    'linebase_removal',
    # Clases principales
    'PPGProcessor',
    'SerialHandler',
]
