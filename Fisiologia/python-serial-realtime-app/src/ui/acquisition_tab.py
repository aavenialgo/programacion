"""
Pestaña de adquisición de datos PPG en tiempo real
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QTextEdit, QLabel, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
from datetime import datetime
from .widgets.acquisition_controls import AcquisitionControls

class AcquisitionTab(QWidget):
    """Pestaña principal para la adquisición y visualización en tiempo real"""
    
    def __init__(self, ppg_processor):
        super().__init__()
        self.ppg_processor = ppg_processor
        self.setup_ui()
        self.setup_connections()
        
        # Timer para actualización de gráficos
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start(25)  # Actualizar cada 25ms (40 FPS)
        #TODO: ajuste a 25 ms como se solicito, ver luego si es necesario cambiar
        
        # Variables para manejo de datos de gráficos
        self.plot_data_cache = {
            'time': [],
            'raw': [],
            'filtered': [],
            'normalized': []
        }
        
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        layout = QHBoxLayout()
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panel de control (izquierda)
        control_widget = self.create_control_panel()
        control_widget.setMaximumWidth(350)
        control_widget.setMinimumWidth(300)
        main_splitter.addWidget(control_widget)
        
        # Panel de gráficos (derecha)
        plots_widget = self.create_plots_panel()
        main_splitter.addWidget(plots_widget)
        
        # Configurar proporciones del splitter
        main_splitter.setSizes([350, 1000])
        
        layout.addWidget(main_splitter)
        self.setLayout(layout)
        
    def create_control_panel(self):
        """Crear panel de control izquierdo"""
        control_widget = QWidget()
        control_layout = QVBoxLayout()
        
        # Controles de adquisición
        self.controls = AcquisitionControls()
        control_layout.addWidget(self.controls)
        
        # Información de estado
        status_group = QGroupBox("Estado del Sistema")
        status_layout = QGridLayout()
        
        status_layout.addWidget(QLabel("Estado:"), 0, 0)
        self.status_label = QLabel("Desconectado")
        self.status_label.setStyleSheet("font-weight: bold; color: #E74C3C;")
        status_layout.addWidget(self.status_label, 0, 1)
        
        status_layout.addWidget(QLabel("Puntos de datos:"), 1, 0)
        self.data_points_label = QLabel("0")
        self.data_points_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.data_points_label, 1, 1)
        
        status_layout.addWidget(QLabel("Tiempo:"), 2, 0)
        self.time_label = QLabel("0.0 s")
        self.time_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.time_label, 2, 1)
        
        status_layout.addWidget(QLabel("Frecuencia Cardíaca:"), 3, 0)
        self.hr_label = QLabel("-- BPM")
        self.hr_label.setStyleSheet("font-weight: bold; color: #27AE60;")
        status_layout.addWidget(self.hr_label, 3, 1)
        
        status_layout.addWidget(QLabel("HRV (RMSSD):"), 4, 0)
        self.hrv_label = QLabel("-- ms")
        self.hrv_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        status_layout.addWidget(self.hrv_label, 4, 1)
        
        status_group.setLayout(status_layout)
        control_layout.addWidget(status_group)
        
        # Log de eventos
        log_group = QGroupBox("Log de Eventos")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        control_layout.addWidget(log_group)
        
        control_widget.setLayout(control_layout)
        return control_widget
        
    def create_plots_panel(self):
        """Crear panel de gráficos"""
        plots_widget = QWidget()
        plots_layout = QVBoxLayout()
        
        # Configurar estilo de PyQtGraph
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        # Gráfico de señal cruda
        self.raw_plot = pg.PlotWidget(title="Señal PPG Cruda")
        self.raw_plot.setLabel('left', 'Amplitud')
        self.raw_plot.setLabel('bottom', 'Tiempo (s)')
        self.raw_plot.showGrid(x=True, y=True)
        self.raw_curve = self.raw_plot.plot(pen=pg.mkPen('#FF6B6B', width=2))
        self.raw_plot.setYRange(-1000, 4000)  # Rango inicial
        plots_layout.addWidget(self.raw_plot)
        
        # Gráfico de señal filtrada
        self.filtered_plot = pg.PlotWidget(title="Señal PPG Filtrada")
        self.filtered_plot.setLabel('left', 'Amplitud')
        self.filtered_plot.setLabel('bottom', 'Tiempo (s)')
        self.filtered_plot.showGrid(x=True, y=True)
        self.filtered_curve = self.filtered_plot.plot(pen=pg.mkPen('#4ECDC4', width=2))
        plots_layout.addWidget(self.filtered_plot)
        
        plots_widget.setLayout(plots_layout)
        return plots_widget
        
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Conexiones del procesador PPG
        self.ppg_processor.new_data_processed.connect(self.update_status)
        self.ppg_processor.analysis_complete.connect(self.on_analysis_complete)
        self.ppg_processor.buffer_full.connect(self.on_buffer_full)
        
    def update_plots(self):
        """Actualiza los gráficos con nuevos datos"""
        try:
            time_data, raw_data, filtered_data, normalized_data = self.ppg_processor.get_display_data(2500)
            
            if len(time_data) > 0:
                # Actualizar curvas
                self.raw_curve.setData(time_data, raw_data)
                self.filtered_curve.setData(time_data, filtered_data)
                
                # Auto-scroll en el eje X (mostrar últimos 30 segundos)
                if time_data:
                    latest_time = time_data[-1]
                    window_size = 30  # segundos
                    start_time = max(0, latest_time - window_size)
                    
                    self.raw_plot.setXRange(start_time, latest_time)
                    self.filtered_plot.setXRange(start_time, latest_time)
                
        except Exception as e:
            self.log_message(f"Error actualizando gráficos: {e}")
            
    def update_status(self):
        """Actualiza la información de estado"""
        stats = self.ppg_processor.get_current_stats()
        
        self.data_points_label.setText(str(stats['data_points']))
        self.time_label.setText(f"{stats['duration']:.1f} s")
        
        if stats['heart_rate'] > 0:
            self.hr_label.setText(f"{stats['heart_rate']:.1f} BPM")
        else:
            self.hr_label.setText("-- BPM")
            
        if stats['hrv'] > 0:
            self.hrv_label.setText(f"{stats['hrv']:.1f} ms")
        else:
            self.hrv_label.setText("-- ms")
            
    def on_analysis_complete(self, results):
        """Manejar resultados de análisis completo"""
        if results and results.get('heart_rate', 0) > 0:
            hr = results.get('heart_rate', 0)
            hrv = results.get('hrv', 0)
            quality = results.get('signal_quality', 'unknown')
            
            self.log_message(f"Análisis: FC={hr:.1f} BPM, HRV={hrv:.1f} ms, Calidad={quality}")
            
    def on_buffer_full(self):
        """Manejar buffer lleno"""
        self.log_message("Buffer lleno - datos más antiguos siendo sobrescritos")
        
    def set_connection_status(self, connected, acquiring=False):
        """Actualizar estado de conexión en la UI"""
        if connected:
            if acquiring:
                self.status_label.setText("Adquiriendo datos")
                self.status_label.setStyleSheet("font-weight: bold; color: #27AE60;")
            else:
                self.status_label.setText("Conectado")
                self.status_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        else:
            self.status_label.setText("Desconectado")
            self.status_label.setStyleSheet("font-weight: bold; color: #E74C3C;")
            
    def log_message(self, message):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll al final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """Limpiar el log"""
        self.log_text.clear()
        self.log_message("Log limpiado")
