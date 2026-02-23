"""
Aplicación principal PPG Analyzer - Versión Refactorizada
"""
import sys
import os
import time
import pandas as pd
import numpy as np
import pyqtgraph as pg
import serial
import threading
import re
import platform
from scipy.signal import find_peaks, savgol_filter, butter, filtfilt

# Importaciones de PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QSplitter, QStatusBar, QTabWidget,
    QLabel, QFileDialog, QSizePolicy, QScrollArea, QTableWidget,
    QTableWidgetItem, QMessageBox, QComboBox, QInputDialog
)
from PyQt5.QtCore import (
    QTimer, QRunnable, QThreadPool, pyqtSignal, QObject, Qt, QSize
)
from PyQt5.QtGui import QFont, QColor

# Importar módulos refactorizados
from .serial_reader import SerialReader
from .ppg_processor import PPGProcessor
from .acquisition_tab import AcquisitionTab
from .analysis_tab import AnalysisTab

# --- Configuraciones de PyQTGraph y Estilo ---
pg.setConfigOption('background', '#FFFFFF')  # Fondo blanco para los gráficos
pg.setConfigOption('foreground', '#333333')  # Eje y texto gris oscuro
pg.setConfigOptions(antialias=True, leftButtonPan=False, useOpenGL=True)

class PPGAnalyzerApp(QMainWindow):
    """Aplicación principal del Analizador PPG - Versión Refactorizada"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador PPG en Tiempo Real - v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Componentes principales
        self.serial_reader = SerialReader()
        self.ppg_processor = PPGProcessor()
        self.serial_port = None
        
        # Estados de la aplicación
        self.connected = False
        self.acquiring = False
        
        self.setup_ui()
        self.setup_connections()
        self.setup_status_bar()
        
    def setup_ui(self):
        """Configura la interfaz del usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Crear pestañas
        self.tab_widget = QTabWidget()
        
        # Pestaña de adquisición (nueva versión refactorizada)
        self.acquisition_tab = AcquisitionTab(self.ppg_processor)
        self.tab_widget.addTab(self.acquisition_tab, "Adquisición de Datos")
        
        # Pestaña de análisis (nueva versión completa)
        self.analysis_tab = AnalysisTab(self.ppg_processor)
        self.tab_widget.addTab(self.analysis_tab, "Análisis de Datos")
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
    def setup_connections(self):
        """Configura las conexiones entre componentes"""
        # Conexiones del lector serie
        self.serial_reader.data_received.connect(self.process_serial_data)
        self.serial_reader.connection_status_changed.connect(self.on_connection_changed)
        self.serial_reader.error_occurred.connect(self.on_serial_error)
        
        # Conexiones de los controles de adquisición
        controls = self.acquisition_tab.controls
        controls.connection_requested.connect(self.connect_serial)
        controls.disconnection_requested.connect(self.disconnect_serial)
        controls.start_acquisition.connect(self.start_acquisition)
        controls.stop_acquisition.connect(self.stop_acquisition)
        controls.reset_data.connect(self.reset_data)
        controls.analyze_data.connect(self.go_to_analysis)  # Nueva conexión
        
    def setup_status_bar(self):
        """Configura la barra de estado"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Etiquetas de estado
        self.connection_status_label = QLabel("Desconectado")
        self.data_rate_label = QLabel("0 pts/s")
        self.hr_status_label = QLabel("FC: -- BPM")
        
        self.status_bar.addWidget(QLabel("Estado:"))
        self.status_bar.addWidget(self.connection_status_label)
        self.status_bar.addPermanentWidget(self.data_rate_label)
        self.status_bar.addPermanentWidget(self.hr_status_label)
        
        # Timer para actualizar velocidad de datos
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(2000)  # Actualizar cada 2 segundos
        self.last_data_count = 0
        
    def connect_serial(self, port, baudrate):
        """Conecta al puerto serie"""
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            self.connected = True
            self.acquisition_tab.controls.set_connection_state(True)
            self.acquisition_tab.log_message(f"Conectado a {port} @ {baudrate}")
            self.connection_status_label.setText("Conectado")
            self.acquisition_tab.set_connection_status(True, False)
            
        except Exception as e:
            error_msg = f"Error de conexión: {e}"
            self.acquisition_tab.log_message(error_msg)
            QMessageBox.critical(self, "Error de Conexión", error_msg)
            
    def disconnect_serial(self):
        """Desconecta el puerto serie"""
        try:
            self.stop_acquisition()
            
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            self.connected = False
            self.acquisition_tab.controls.set_connection_state(False)
            self.acquisition_tab.log_message("Desconectado")
            self.connection_status_label.setText("Desconectado")
            self.acquisition_tab.set_connection_status(False, False)
            
        except Exception as e:
            error_msg = f"Error al desconectar: {e}"
            self.acquisition_tab.log_message(error_msg)
            
    def start_acquisition(self):
        """Inicia la adquisición de datos"""
        if self.connected and self.serial_port and self.serial_port.is_open:
            try:
                self.serial_reader.start_reading(self.serial_port)
                self.ppg_processor.start_processing()
                self.acquiring = True
                
                self.acquisition_tab.controls.set_acquisition_state(True)
                self.acquisition_tab.log_message("Adquisición iniciada")
                self.acquisition_tab.set_connection_status(True, True)
                
            except Exception as e:
                error_msg = f"Error iniciando adquisición: {e}"
                self.acquisition_tab.log_message(error_msg)
                QMessageBox.critical(self, "Error", error_msg)
        else:
            QMessageBox.warning(self, "Advertencia", "Debe conectarse primero al puerto serie")
            
    def stop_acquisition(self):
        """Detiene la adquisición de datos"""
        try:
            self.serial_reader.stop_reading()
            self.ppg_processor.stop_processing()
            self.acquiring = False
            
            self.acquisition_tab.controls.set_acquisition_state(False)
            self.acquisition_tab.log_message("Adquisición detenida")
            
            if self.connected:
                self.acquisition_tab.set_connection_status(True, False)
            
        except Exception as e:
            error_msg = f"Error deteniendo adquisición: {e}"
            self.acquisition_tab.log_message(error_msg)
            
    def reset_data(self):
        """Resetea todos los datos"""
        try:
            self.ppg_processor.reset_data()
            self.acquisition_tab.log_message("Datos reseteados")
            
            # Limpiar gráfico
            self.acquisition_tab.raw_curve.setData([], [])
            
        except Exception as e:
            error_msg = f"Error reseteando datos: {e}"
            self.acquisition_tab.log_message(error_msg)
            
    def go_to_analysis(self):
        """Cambia a la pestaña de análisis y carga datos de adquisición"""
        try:
            # Cambiar a la pestaña de análisis
            self.tab_widget.setCurrentWidget(self.analysis_tab)
            
            # Cargar datos de adquisición en la pestaña de análisis
            self.analysis_tab.load_acquisition_data()
            
            self.acquisition_tab.log_message("Cambiando a pestaña de análisis")
            
        except Exception as e:
            error_msg = f"Error cambiando a análisis: {e}"
            self.acquisition_tab.log_message(error_msg)
            
    def process_serial_data(self, data_line):
        """Procesa una línea de datos recibida por serie"""
        try:
            # Parsear datos usando el SerialReader
            parsed_data = self.serial_reader.parse_data_line(data_line)
            
            if parsed_data is not None:
                # Enviar datos al procesador PPG (solo canal raw)
                self.ppg_processor.add_data_point(parsed_data)
            else:
                # Si no es el formato esperado, intentar como número simple
                try:
                    value = float(data_line.strip())
                    self.ppg_processor.add_data_point(value)
                except ValueError:
                    pass  # Ignorar líneas que no son números
                    
        except Exception as e:
            self.acquisition_tab.log_message(f"Error procesando datos: {e}")
            
    def on_connection_changed(self, connected):
        """Maneja el cambio en estado de conexión del SerialReader"""
        status = "Conectado" if connected else "Desconectado"
        self.connection_status_label.setText(status)
        
    def on_serial_error(self, error_msg):
        """Maneja el error en comunicación serie"""
        self.acquisition_tab.log_message(f"Error serie: {error_msg}")
        self.disconnect_serial()
        
    def update_status_bar(self):
        """Actualiza la barra de estado"""
        try:
            # Calcular velocidad de datos
            current_count = len(self.ppg_processor.time_buffer)
            data_rate = (current_count - self.last_data_count) / 2.0  # pts/s
            self.last_data_count = current_count
            self.data_rate_label.setText(f"{data_rate:.1f} pts/s")
            
            # Actualizar frecuencia cardíaca
            stats = self.ppg_processor.get_current_stats()
            if stats['heart_rate'] > 0:
                self.hr_status_label.setText(f"FC: {stats['heart_rate']:.1f} BPM")
            else:
                self.hr_status_label.setText("FC: -- BPM")
                
        except Exception as e:
            pass  # Ignorar errores de actualización de estado
            
    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        try:
            self.stop_acquisition()
            self.disconnect_serial()
            event.accept()
        except Exception as e:
            print(f"Error cerrando aplicación: {e}")
            event.accept()


def main():
    """Función principal para ejecutar la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F8F9FA;
        }
        QTabWidget::pane {
            border: 1px solid #BDC3C7;
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
        QGroupBox {
            font-weight: bold;
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    # Crear y mostrar ventana principal
    window = PPGAnalyzerApp()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
