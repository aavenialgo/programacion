"""
Widget de controles para la adquisición de datos
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QComboBox, QLabel, QLineEdit, QSpinBox, QGroupBox,
                            QMessageBox)
from PyQt5.QtCore import pyqtSignal
import serial.tools.list_ports

class AcquisitionControls(QWidget):
    """Widget de control para la adquisición de datos del puerto serie"""
    
    # Señales
    connection_requested = pyqtSignal(str, int)  # puerto, baudrate
    disconnection_requested = pyqtSignal()
    start_acquisition = pyqtSignal()
    stop_acquisition = pyqtSignal()
    reset_data = pyqtSignal()
    analyze_data = pyqtSignal()  # Nueva señal para análisis
    
    def __init__(self):
        super().__init__()
        self.connected = False
        self.acquiring = False
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Grupo de conexión serie
        connection_group = QGroupBox("Conexión Serie")
        connection_layout = QVBoxLayout()
        
        # Puerto serie
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_ports)
        refresh_btn.setMaximumWidth(80)
        port_layout.addWidget(refresh_btn)
        connection_layout.addLayout(port_layout)
        
        # Baudrate
        baudrate_layout = QHBoxLayout()
        baudrate_layout.addWidget(QLabel("Baudrate:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baudrate_combo.setCurrentText('115200')
        baudrate_layout.addWidget(self.baudrate_combo)
        connection_layout.addLayout(baudrate_layout)
        
        # Botones de conexión
        connection_buttons = QHBoxLayout()
        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self.toggle_connection)
        connection_buttons.addWidget(self.connect_btn)
        
        connection_layout.addLayout(connection_buttons)
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Grupo de adquisición
        acquisition_group = QGroupBox("Control de Adquisición")
        acquisition_layout = QVBoxLayout()
        
        # Botones de control
        control_buttons = QHBoxLayout()
        self.start_btn = QPushButton("Iniciar Adquisición")
        self.start_btn.clicked.connect(self.toggle_acquisition)
        self.start_btn.setEnabled(False)
        control_buttons.addWidget(self.start_btn)
        
        acquisition_layout.addLayout(control_buttons)
        
        # Botón de reset
        reset_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset Datos")
        self.reset_btn.clicked.connect(self.reset_data.emit)
        reset_layout.addWidget(self.reset_btn)
        acquisition_layout.addLayout(reset_layout)
        
        # Botón de análisis
        analysis_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analizar Datos")
        self.analyze_btn.clicked.connect(self.analyze_data.emit)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        analysis_layout.addWidget(self.analyze_btn)
        acquisition_layout.addLayout(analysis_layout)
        
        acquisition_group.setLayout(acquisition_layout)
        layout.addWidget(acquisition_group)
        
        # Espaciador
        layout.addStretch()
        
        self.setLayout(layout)
        
    def refresh_ports(self):
        """Actualiza la lista de puertos disponibles"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.port_combo.addItem("No hay puertos disponibles")
            return
            
        for port in ports:
            display_text = f"{port.device}"
            if port.description and port.description != 'n/a':
                display_text += f" - {port.description}"
            self.port_combo.addItem(display_text)
            
    def toggle_connection(self):
        """Alterna el estado de conexión"""
        if not self.connected:
            port_text = self.port_combo.currentText()
            if not port_text or "No hay puertos" in port_text:
                QMessageBox.warning(self, "Error", "Seleccione un puerto serie válido")
                return
                
            # Extraer solo el nombre del puerto
            port = port_text.split(" - ")[0]
            
            try:
                baudrate = int(self.baudrate_combo.currentText())
            except ValueError:
                QMessageBox.warning(self, "Error", "Baudrate inválido")
                return
                
            self.connection_requested.emit(port, baudrate)
        else:
            self.disconnection_requested.emit()
            
    def toggle_acquisition(self):
        """Alterna el estado de adquisición"""
        if not self.acquiring:
            self.start_acquisition.emit()
        else:
            self.stop_acquisition.emit()
            
    def set_connection_state(self, connected):
        """Actualiza el estado de conexión"""
        self.connected = connected
        if connected:
            self.connect_btn.setText("Desconectar")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
            """)
            self.start_btn.setEnabled(True)
            self.port_combo.setEnabled(False)
            self.baudrate_combo.setEnabled(False)
        else:
            self.connect_btn.setText("Conectar")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            self.start_btn.setEnabled(False)
            self.port_combo.setEnabled(True)
            self.baudrate_combo.setEnabled(True)
            self.set_acquisition_state(False)
            
    def set_acquisition_state(self, acquiring):
        """Actualiza el estado de adquisición"""
        self.acquiring = acquiring
        if acquiring:
            self.start_btn.setText("Detener Adquisición")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E67E22;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D35400;
                }
            """)
        else:
            self.start_btn.setText("Iniciar Adquisición")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
