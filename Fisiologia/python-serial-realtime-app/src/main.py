"""
Archivo principal de la aplicación PPG Analyzer
"""
import sys
import os

# Agregar el directorio src al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from ui.interfaz2 import PPGAnalyzerApp  # Temporalmente usando interfaz2
from config.settings import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT

def main():
    """Función principal de la aplicación"""
    app = QApplication(sys.argv)
    
    # Crear ventana principal
    window = PPGAnalyzerApp()
    window.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
