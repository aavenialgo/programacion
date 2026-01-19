"""
Submódulo widgets - Componentes reutilizables de la interfaz.

Este módulo contiene widgets personalizados para:
- Controles de adquisición (acquisition_controls.py)
- Gráficos PPG (ppg_plot_widget.py)
- Panel de estado (status_panel.py)
"""

# Importar widgets
try:
    from .acquisition_controls import AcquisitionControls
except ImportError as e:
    print(f"Warning: No se pudo importar AcquisitionControls: {e}")

try:
    from .ppg_plot_widget import PPGPlotWidget
except ImportError as e:
    print(f"Warning: No se pudo importar PPGPlotWidget: {e}")

try:
    from .status_panel import StatusPanel
except ImportError as e:
    print(f"Warning: No se pudo importar StatusPanel: {e}")

__all__ = [
    'AcquisitionControls',
    'PPGPlotWidget',
    'StatusPanel',
]