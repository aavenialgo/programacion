"""
Estilos y configuraciones para la interfaz de usuario
"""
import pyqtgraph as pg
from ..config.settings import COLORS

def configure_pyqtgraph():
    """Configura los estilos globales de PyQTGraph"""
    pg.setConfigOption('background', COLORS['background'])
    pg.setConfigOption('foreground', COLORS['foreground'])
    pg.setConfigOptions(antialias=True, leftButtonPan=False, useOpenGL=True)

# Estilos CSS para widgets Qt
BUTTON_STYLE = """
QPushButton {
    background-color: #4ECDC4;
    border: 1px solid #3D9991;
    border-radius: 5px;
    padding: 8px 16px;
    color: white;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #45B7D1;
    border-color: #3A9BC1;
}
QPushButton:pressed {
    background-color: #3A9BC1;
}
QPushButton:disabled {
    background-color: #CCCCCC;
    color: #666666;
    border-color: #AAAAAA;
}
"""

CONNECT_BUTTON_STYLE = """
QPushButton {
    background-color: #2ECC71;
    border: 1px solid #27AE60;
    border-radius: 5px;
    padding: 8px 16px;
    color: white;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #27AE60;
}
QPushButton:pressed {
    background-color: #229954;
}
"""

DISCONNECT_BUTTON_STYLE = """
QPushButton {
    background-color: #E74C3C;
    border: 1px solid #C0392B;
    border-radius: 5px;
    padding: 8px 16px;
    color: white;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #C0392B;
}
QPushButton:pressed {
    background-color: #A93226;
}
"""

LINEEDIT_STYLE = """
QLineEdit {
    border: 2px solid #BDC3C7;
    border-radius: 5px;
    padding: 5px;
    font-size: 11px;
    background-color: white;
}
QLineEdit:focus {
    border-color: #3498DB;
}
"""

LABEL_STYLE = """
QLabel {
    color: #2C3E50;
    font-size: 11px;
    font-weight: bold;
}
"""

TAB_STYLE = """
QTabWidget::pane {
    border: 1px solid #BDC3C7;
    border-radius: 5px;
    background-color: white;
}
QTabBar::tab {
    background-color: #ECF0F1;
    border: 1px solid #BDC3C7;
    padding: 8px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: white;
    border-bottom: none;
    font-weight: bold;
}
QTabBar::tab:hover {
    background-color: #D5DBDB;
}
"""

def get_plot_pen(color_name, width=2):
    """Obtiene un pen para gráficos con el color especificado"""
    return pg.mkPen(color=COLORS.get(color_name, '#000000'), width=width)
