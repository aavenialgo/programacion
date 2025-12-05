"""
Paquete de análisis de señales PPG en tiempo real.

Este paquete contiene módulos para:
- Análisis de señales PPG (ppg_analisis.py)
- Visualización en tiempo real (graficador.py)  
- Comunicación serial (serial_handler.py)
- Utilidades de procesamiento de señales

Autor: Andrés Venialgo
Fecha: Noviembre 2025
"""


# Importar las funciones principales para facilitar el acceso
try:
    from .core.ppg_analisis import (
        get_temporal_features,
        get_dc_component,
        get_ac_component
    )
except ImportError as e:
    print(f"Warning: No se pudo importar from core.ppg_analisis: {e}")

try:
    from .data.read_data import load_ppg_from_csv
except ImportError as e:
    print(f"Warning: No se pudo importar from data.read_data: {e}")

# Definir qué se exporta cuando se hace "from src import *"
__all__ = [
    # Funciones de análisis PPG
    'get_temporal_features',
    'get_dc_component',
    'get_ac_component',
    # Funciones de carga de datos
    'load_ppg_from_csv',
]

# Metadatos del paquete
__author__ = "Andrés Venialgo"
__email__ = "andres.venialgo@ingenieria.uner.edu.ar"  # Cambia por tu email
__description__ = "Paquete para análisis de señales PPG en tiempo real"