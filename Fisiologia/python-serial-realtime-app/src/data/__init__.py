"""
Módulo data - Funciones para lectura y escritura de datos.

Este módulo contiene:
- Lectura de archivos CSV (read_data.py)
- Gestión de datos de señales PPG
"""

from .read_data import load_ppg_from_csv

# TODO: Modularizar funcionalidad de escritura
# from .write_data import save_ppg_to_csv, save_analysis_results

__all__ = [
    'load_ppg_from_csv',
    # 'save_ppg_to_csv',
    # 'save_analysis_results',
]