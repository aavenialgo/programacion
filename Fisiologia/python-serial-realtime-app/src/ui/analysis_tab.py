"""
Este archivo implementa la pestaña de adquisición de datos
en tiempo real utilizando PyQt5 y PyQtGraph.

"""
import pandas as pd
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QCheckBox, QGridLayout, QTextEdit
)
from PyQt5.QtCore import Qt
from datetime import datetime

# Importar el filtro
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.filter import apply_filter, linebase_removal

class AnalysisTab(QWidget):
    """Pestaña para el análisis de datos"""
    
    def __init__(self, ppg_processor):
        """
        Constructor de la pestaña de análisis
        
        :param ppg_processor: Instancia del procesador PPG 
        para obtener datos de adquisición
        """
        super().__init__()
        self.ppg_processor = ppg_processor
        self.current_data = None  # Datos cargados o transferidos
        self.filtered_data = None  # Datos filtrados
        self.baseline_removed = False
        self.fiducials = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configuracion de la interfaz de usuario"""
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
        """ Crea el panel de control """
        control_widget = QWidget()
        control_layout = QVBoxLayout()
        
        # Grupo de carga de datos
        data_group = QGroupBox("Cargar Datos")
        data_layout = QVBoxLayout()
        
        # Botón para cargar CSV
        self.load_csv_btn = QPushButton("Cargar archivo CSV")
        self.load_csv_btn.clicked.connect(self.load_csv_file)
        self.load_csv_btn.setStyleSheet("""
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
        data_layout.addWidget(self.load_csv_btn)
        
        # Botón para usar los datos de adquisición
        self.use_acquisition_btn = QPushButton("Usar datos de adquisición")
        self.use_acquisition_btn.clicked.connect(self.load_acquisition_data)
        self.use_acquisition_btn.setStyleSheet("""
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
        data_layout.addWidget(self.use_acquisition_btn)
        
        # Información de los datos cargados
        self.data_info_label = QLabel("No hay datos cargados")
        self.data_info_label.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        data_layout.addWidget(self.data_info_label)

        # Botón para limpiar / resetear datos cargados
        self.reset_btn = QPushButton("Limpiar datos")
        self.reset_btn.setEnabled(False)
        self.reset_btn.clicked.connect(self.clear_data)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        data_layout.addWidget(self.reset_btn)
        
        data_group.setLayout(data_layout)
        control_layout.addWidget(data_group)
        
        # Grupo de filtrado
        filter_group = QGroupBox("Filtro Butterworth")
        filter_layout = QGridLayout()
        
        # Frecuencia de corte baja
        filter_layout.addWidget(QLabel("Freq. corte baja (Hz):"), 0, 0)
        self.lowcut_spin = QDoubleSpinBox()
        self.lowcut_spin.setRange(0.1, 10.0)
        self.lowcut_spin.setValue(0.5)
        self.lowcut_spin.setSingleStep(0.1)
        self.lowcut_spin.setDecimals(1)
        filter_layout.addWidget(self.lowcut_spin, 0, 1)
        
        # Frecuencia de corte alta
        filter_layout.addWidget(QLabel("Freq. corte alta (Hz):"), 1, 0)
        self.highcut_spin = QDoubleSpinBox()
        self.highcut_spin.setRange(1.0, 50.0)
        self.highcut_spin.setValue(5.0)
        self.highcut_spin.setSingleStep(0.1)
        self.highcut_spin.setDecimals(1)
        filter_layout.addWidget(self.highcut_spin, 1, 1)
        
        # Orden del filtro
        filter_layout.addWidget(QLabel("Orden:"), 2, 0)
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(4)
        filter_layout.addWidget(self.order_spin, 2, 1)
        
        # Frecuencia de muestreo
        filter_layout.addWidget(QLabel("Freq. muestreo (Hz):"), 3, 0)
        self.fs_spin = QSpinBox()
        self.fs_spin.setRange(50, 1000)
        self.fs_spin.setValue(100)
        filter_layout.addWidget(self.fs_spin, 3, 1)
        
        # Botón aplicar filtro
        self.apply_filter_btn = QPushButton("Aplicar Filtro")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.apply_filter_btn.setEnabled(False)
        self.apply_filter_btn.setStyleSheet("""
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
        filter_layout.addWidget(self.apply_filter_btn, 4, 0, 1, 2)
        
        filter_group.setLayout(filter_layout)
        control_layout.addWidget(filter_group)
        
        # Grupo de procesamiento
        process_group = QGroupBox("Procesamiento")
        process_layout = QVBoxLayout()
        
        # Checkbox para sacar línea base
        self.baseline_checkbox = QCheckBox("Sacar línea base")
        self.baseline_checkbox.stateChanged.connect(self.toggle_baseline_removal)
        process_layout.addWidget(self.baseline_checkbox)

        # Botón para detectar puntos fiduciales en la señal PPG
        self.detect_fiducials_btn = QPushButton("Detectar puntos fiduciales")
        self.detect_fiducials_btn.setEnabled(False)
        self.detect_fiducials_btn.clicked.connect(self.detect_fiducials)
        self.detect_fiducials_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
        """)
        process_layout.addWidget(self.detect_fiducials_btn)
        
        process_group.setLayout(process_layout)
        control_layout.addWidget(process_group)
        
        # Log de análisis
        log_group = QGroupBox("Log de Análisis")
        log_layout = QVBoxLayout()
        
        self.analysis_log = QTextEdit()
        self.analysis_log.setMaximumHeight(150)
        self.analysis_log.setReadOnly(True)
        self.analysis_log.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.analysis_log)
        log_group.setLayout(log_layout)
        control_layout.addWidget(log_group)
        
        # Espaciador
        control_layout.addStretch()
        
        control_widget.setLayout(control_layout)
        return control_widget
        
    def create_plots_panel(self):
        """Crea el panel de gráficos"""
        plots_widget = QWidget()
        plots_layout = QVBoxLayout()
        
        # Configurar estilo de PyQtGraph
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        # Gráfico de señal original
        self.original_plot = pg.PlotWidget(title="Señal Original")
        self.original_plot.setLabel('left', 'Amplitud')
        self.original_plot.setLabel('bottom', 'Tiempo (s)')
        self.original_plot.showGrid(x=True, y=True)
        self.original_curve = self.original_plot.plot(pen=pg.mkPen('#FF6B6B', width=2))
        plots_layout.addWidget(self.original_plot)
        
        # Gráfico de señal filtrada
        self.filtered_plot = pg.PlotWidget(title="Señal Filtrada")
        self.filtered_plot.setLabel('left', 'Amplitud')
        self.filtered_plot.setLabel('bottom', 'Tiempo (s)')
        self.filtered_plot.showGrid(x=True, y=True)
        self.filtered_curve = self.filtered_plot.plot(pen=pg.mkPen('#4ECDC4', width=2))
        self.fiducial_scatter = pg.ScatterPlotItem(symbol='o', size=9, pen=pg.mkPen(None), brush=pg.mkBrush('#EF4444'))
        self.filtered_plot.addItem(self.fiducial_scatter)
        plots_layout.addWidget(self.filtered_plot)
        
        plots_widget.setLayout(plots_layout)
        return plots_widget
        
    def load_csv_file(self):
        """Carga los datos desde archivo CSV"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Seleccionar archivo CSV", "", "Archivos CSV (*.csv)"
        )
        
        if file_path:
            try:
                # Intentar cargar el CSV
                df = pd.read_csv(file_path)
                
                # Asumir que la primera columna es tiempo y la segunda es la señal
                if df.shape[1] >= 2:
                    self.current_data = df.iloc[:, 1].values  # Segunda columna como señal
                    self.time_data = df.iloc[:, 0].values     # Primera columna como tiempo
                elif df.shape[1] == 1:
                    self.current_data = df.iloc[:, 0].values  # Una sola columna
                    self.time_data = np.arange(len(self.current_data))  # Crear tiempo
                else:
                    raise ValueError("El archivo debe tener al menos una columna de datos")
                
                # Actualizar UI
                self.data_info_label.setText(f"CSV cargado: {len(self.current_data)} puntos")
                self.apply_filter_btn.setEnabled(True)
                self.detect_fiducials_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.clear_fiducials()
                
                # Mostrar datos originales
                self.update_original_plot()
                
                # Log
                self.log_message(f"Archivo CSV cargado: {file_path}")
                self.log_message(f"Datos: {len(self.current_data)} puntos")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error cargando archivo CSV:\n{e}")
                self.log_message(f"Error cargando CSV: {e}")
                
    def load_acquisition_data(self):
        """Carga de datos de la adquisición en tiempo real"""
        try:
            # Obtener datos del procesador PPG (solo canal raw)
            time_data, raw_data = self.ppg_processor.get_display_data()
            
            if len(raw_data) > 0:
                self.current_data = np.array(raw_data)
                self.time_data = np.array(time_data)
                
                # Actualizar UI
                self.data_info_label.setText(f"Datos de adquisición: {len(self.current_data)} puntos")
                self.apply_filter_btn.setEnabled(True)
                self.detect_fiducials_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.clear_fiducials()
                
                # Mostrar los datos originales
                self.update_original_plot()
                
                # Log
                self.log_message(f"Datos de adquisición cargados: {len(self.current_data)} puntos")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay datos de adquisición disponibles")
                self.log_message("No hay datos de adquisición disponibles")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando datos de adquisición:\n{e}")
            self.log_message(f"Error cargando datos de adquisición: {e}")
    #TODO: ver si funciona     
    def apply_filter(self):
        """Aplicar filtro Butterworth a los datos"""
        try:
            # Obtener parámetros del filtro
            lowcut = self.lowcut_spin.value()
            highcut = self.highcut_spin.value()
            fs = self.fs_spin.value()
            order = self.order_spin.value()
            
            # Aplicar filtro (las validaciones están en el módulo filter)
            self.filtered_data = apply_filter(self.current_data, lowcut, highcut, fs, order)
            
            # Actualizar el gráfico filtrado
            self.update_filtered_plot()
            
            # Log
            self.log_message(f"Filtro aplicado: {lowcut}-{highcut} Hz, orden {order}")
            
        except ValueError as e:
            # Errores de validación de parámetros
            QMessageBox.warning(self, "Error de validación", str(e))
            self.log_message(f"Error de validación: {e}")
        except Exception as e:
            # Otros errores
            QMessageBox.critical(self, "Error", f"Error aplicando filtro:\n{e}")
            self.log_message(f"Error aplicando filtro: {e}")
            
    def toggle_baseline_removal(self, state):
        """Alternar eliminación de línea base"""
        if state == Qt.Checked:
            if self.filtered_data is not None:
                #TODO: ver si esta bien implementado 
                self.sacar_linea_base()
                self.baseline_removed = True
                self.log_message("Línea base eliminada")
            else:
                self.log_message("Primero debe aplicar un filtro")
                self.baseline_checkbox.setChecked(False)
        else:
            # Restaurar datos filtrados originales
            if self.filtered_data is not None:
                self.update_filtered_plot()
                self.baseline_removed = False
                self.log_message("Línea base restaurada")
                
    def sacar_linea_base(self):
        """Función para eliminar línea base"""
        self.filtered_data = linebase_removal(self.filtered_data, self.fs_spin.value())
        self.update_filtered_plot()
        #TODO: ver si esta bien implementado
        
    def update_original_plot(self): 
        """Actualiza el gráfico de señal original""" 
        if self.current_data is not None:
            self.original_curve.setData(self.time_data, self.current_data)
            
    def update_filtered_plot(self):
        """Actualizar gráfico de señal filtrada"""
        if self.filtered_data is not None:
            self.filtered_curve.setData(self.time_data, self.filtered_data)
            
    def log_message(self, message):
        """Agrega el mensaje al log de análisis"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.analysis_log.append(formatted_message)
        
        # Auto-scroll al final
        scrollbar = self.analysis_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_data(self):
        """Limpia todos los datos"""
        self.current_data = None
        self.filtered_data = None
        self.time_data = None
        self.baseline_removed = False
        
        # Limpia los gráficos
        self.original_curve.setData([], [])
        self.filtered_curve.setData([], [])
        
        # Actualizar UI
        self.data_info_label.setText("No hay datos cargados")
        self.apply_filter_btn.setEnabled(False)
        self.baseline_checkbox.setChecked(False)
        self.detect_fiducials_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.clear_fiducials()
        
        self.log_message("Datos limpiados")

    def detect_fiducials(self):
        """Detecta puntos fiduciales (pico sistólico y muesca dicrotica) en la señal PPG filtrada."""
        if self.current_data is None or getattr(self, 'time_data', None) is None:
            QMessageBox.warning(self, "Sin datos", "Cargue datos antes de detectar fiduciales")
            return

        if self.filtered_data is None:
            QMessageBox.warning(self, "Sin filtro", "Aplique un filtro antes de detectar fiduciales")
            return

        signal = self.filtered_data
        time_data = self.time_data

        analysis, _ = self.ppg_processor.analyze_segment(time_data, signal)
        if not analysis:
            QMessageBox.information(self, "Sin resultado", "No se pudieron detectar fiduciales en esta ventana")
            return

        fid = analysis.get('fiducials', {})
        systolic_t = fid.get('systolic_peak', [])
        notch_t = fid.get('dicrotic_notch', [])

        times = []
        values = []

        def add_points(t_array):
            for t_val in np.atleast_1d(t_array):
                idx = int(np.argmin(np.abs(time_data - t_val)))
                if 0 <= idx < len(signal):
                    times.append(time_data[idx])
                    values.append(signal[idx])

        add_points(systolic_t)
        add_points(notch_t)

        self.fiducials = {'time': times, 'value': values}
        self.update_fiducial_plot()

        self.log_message(f"Fiduciales detectados: {len(times)} puntos (picos sistólicos y muescas dicroticas)")

    def update_fiducial_plot(self):
        """Actualiza la capa de puntos fiduciales sobre la señal PPG."""
        if not self.fiducials or not self.fiducials.get('time'):
            self.fiducial_scatter.clear()
            return

        spots = [{'pos': (t, y)} for t, y in zip(self.fiducials['time'], self.fiducials['value'])]
        self.fiducial_scatter.setData(spots)

    def clear_fiducials(self):
        """Limpia los puntos fiduciales del gráfico."""
        self.fiducials = None
        self.fiducial_scatter.clear()
