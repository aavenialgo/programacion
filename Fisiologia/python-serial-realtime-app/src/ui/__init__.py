"""
Módulo ui - Interfaz gráfica de usuario con PyQt5.

Este módulo contiene:
- Ventana principal (main_window.py)
- Pestaña de adquisición (acquisition_tab.py)
- Pestaña de análisis (analysis_tab.py)
- Widgets personalizados (widgets/)
"""

# Importar ventana principal

# Importar pestañas
try:
    from .acquisition_tab import AcquisitionTab
except ImportError as e:
    print(f"Warning: No se pudo importar AcquisitionTab: {e}")

try:
    from .analysis_tab import AnalysisTab
except ImportError as e:
    print(f"Warning: No se pudo importar AnalysisTab: {e}")

# Importar widgets personalizados
try:
    from .widgets.acquisition_controls import AcquisitionControls
except ImportError as e:
    print(f"Warning: No se pudo importar AcquisitionControls: {e}")

__all__ = [
    # Ventana principal
    'MainWindow',
    # Pestañas
    'AcquisitionTab',
    'AnalysisTab',
    # Widgets
    'AcquisitionControls',
]