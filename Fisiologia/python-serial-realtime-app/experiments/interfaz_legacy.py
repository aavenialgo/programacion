import sys
import serial
import threading
import time
import csv
import os
from collections import deque
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import re
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
from filter import filterPassBand, moving_average

# === CONFIGURACION ===
PORT = '/dev/ttyUSB0'
BAUD = 115200
FS = 125  # frecuencia de muestreo (Hz)
MAX_POINTS = FS * 60  # Buffer de 60 segundos
DEFAULT_WINDOW_SIZE = 5  # segundos

class SerialReader(threading.Thread):
    """Clase para leer datos del puerto serie en un hilo separado"""
    
    def __init__(self, port, baud):
        super().__init__(daemon=True)
        self.ser = None
        self.port = port
        self.baud = baud
        self.lock = threading.Lock()
        self.running = False
        self.paused = False
        self.buffer = []
        
        # Regex para extraer los valores
        self.pattern = re.compile(r"Crudo:(-?\d+(?:\.\d+)?),Filtrado:(-?\d+(?:\.\d+)?),Normalizado:(-?\d+(?:\.\d+)?)", re.IGNORECASE)
    
    def connect(self):
        """Conectar al puerto serie"""
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            return True
        except Exception as e:
            print(f"Error conectando al puerto serie: {e}")
            return False
    
    def start_acquisition(self):
        """Iniciar adquisicion de datos"""
        self.running = True
        self.paused = False
        if not self.is_alive():
            self.start()
    
    def pause_acquisition(self):
        """Pausar adquisicion de datos"""
        self.paused = True
    
    def resume_acquisition(self):
        """Reanudar adquisicion de datos"""
        self.paused = False
    
    def stop_acquisition(self):
        """Detener adquisicion de datos"""
        self.running = False
        self.paused = False  # Asegurar que no quede pausado
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception as e:
                print(f"Error cerrando puerto serie: {e}")
        
        # Esperar a que el hilo termine
        if self.is_alive():
            try:
                self.join(timeout=2.0)  # Esperar máximo 2 segundos
            except Exception as e:
                print(f"Error esperando fin de hilo: {e}")
    
    def run(self):
        while self.running:
            try:
                if not self.paused and self.ser and self.ser.is_open:
                    line = self.ser.readline().decode(errors='ignore').strip()
                    match = self.pattern.search(line)
                    if match:
                        crudo_val = float(match.group(1))
                        filtrado_val = float(match.group(2))
                        normalizado_val = float(match.group(3))
                        
                        ts = time.time()
                        with self.lock:
                            self.buffer.append((ts, crudo_val, filtrado_val, normalizado_val))
                else:
                    time.sleep(0.01)
            except Exception as e:
                print(f"Error leyendo datos: {e}")
                time.sleep(0.1)
    
    def get_data(self):
        """Obtener datos del buffer"""
        with self.lock:
            data = self.buffer[:]
            self.buffer.clear()
        return data

class PPGAnalyzer:
    """Clase para analisis de señales PPG"""
    
    @staticmethod
    def calculate_amplitude(data):
        """Calcular amplitud de la señal"""
        if len(data) < 2:
            return 0
        return np.max(data) - np.min(data)
    
    @staticmethod
    def calculate_frequency(data, fs):
        """Calcular frecuencia cardiaca promedio"""
        if len(data) < fs:
            return 0
        peaks, _ = find_peaks(data, height=0.5, distance=fs*0.5, prominence=0.3)
        peak_intervals = np.diff(peaks) / fs

        hr_inst = 60 / peak_intervals  # BPM instantáneos
        frequency_mean = np.mean(hr_inst)
        return frequency_mean
    
    @staticmethod
    def detect_peaks(data, prominence=0.1):
        """Detectar picos en la señal"""
        if len(data) < 10:
            return []
        peaks, _ = signal.find_peaks(data, prominence=prominence)
        return peaks

class MainWindow(QtWidgets.QMainWindow):
    """Ventana principal de la aplicacion"""
    
    def __init__(self):
        super().__init__()
        #self.serial_reader = SerialReader(PORT, BAUD)
        self.serial_reader = None
        self.analyzer = PPGAnalyzer()
        
        # Buffers de datos
        self.data_crudo = deque(maxlen=MAX_POINTS)
        self.data_filtrado = deque(maxlen=MAX_POINTS)
        self.data_normalizado = deque(maxlen=MAX_POINTS)
        self.time_data = deque(maxlen=MAX_POINTS)
        
        # Configuracion de timestamps relativos
        self.start_timestamp = None  # Timestamp del inicio de adquisicion
        
        # Configuracion de visualizacion
        self.window_size = DEFAULT_WINDOW_SIZE
        self.current_channel = "filtrado"  # canal por defecto
        self.is_paused_display = False
        
        # Configuracion de filtros
        self.filter_enabled = False
        self.filter_lowcut = 0.5
        self.filter_highcut = 15.0
        self.filter_order = 4
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """Inicializar la interfaz de usuario"""
        self.setWindowTitle("Monitor PPG - Analisis de Señales")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        
        # Panel de control izquierdo
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # Panel de graficos derecho
        plot_panel = self.create_plot_panel()
        main_layout.addWidget(plot_panel, 4)
        
    def create_control_panel(self):
        """Crear panel de controles"""
        # Crear un scroll area para el panel de controles
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setMaximumWidth(370)  # Un poco mas ancho para incluir el scrollbar
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # Widget interno que contendra todos los controles
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        
        # === Seccion de Conexion ===
        conn_group = QtWidgets.QGroupBox("Conexion Serie")
        conn_layout = QtWidgets.QVBoxLayout(conn_group)
        
        self.port_combo = QtWidgets.QComboBox()
        self.port_combo.addItems(['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0'])
        self.port_combo.setCurrentText(PORT)
        conn_layout.addWidget(QtWidgets.QLabel("Puerto:"))
        conn_layout.addWidget(self.port_combo)
        
        self.connect_btn = QtWidgets.QPushButton("Conectar")
        self.connect_btn.clicked.connect(self.connect_serial)
        conn_layout.addWidget(self.connect_btn)
        
        self.status_label = QtWidgets.QLabel("Desconectado")
        self.status_label.setStyleSheet("color: red")
        conn_layout.addWidget(self.status_label)
        
        layout.addWidget(conn_group)
        
        # === Seccion de Control de Adquisicion ===
        acq_group = QtWidgets.QGroupBox("Control de Adquisicion")
        acq_layout = QtWidgets.QVBoxLayout(acq_group)
        
        self.start_btn = QtWidgets.QPushButton("Iniciar")
        self.start_btn.clicked.connect(self.start_acquisition)
        self.start_btn.setEnabled(False)
        
        self.pause_btn = QtWidgets.QPushButton("Pausar")
        self.pause_btn.clicked.connect(self.pause_acquisition)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QtWidgets.QPushButton("Detener")
        self.stop_btn.clicked.connect(self.stop_acquisition)
        self.stop_btn.setEnabled(False)
        
        acq_layout.addWidget(self.start_btn)
        acq_layout.addWidget(self.pause_btn)
        acq_layout.addWidget(self.stop_btn)
        
        layout.addWidget(acq_group)
        
        # === Seccion de Visualizacion ===
        vis_group = QtWidgets.QGroupBox("Visualizacion")
        vis_layout = QtWidgets.QVBoxLayout(vis_group)
        
        vis_layout.addWidget(QtWidgets.QLabel("Canal:"))
        self.channel_combo = QtWidgets.QComboBox()
        self.channel_combo.addItems(["crudo", "filtrado", "normalizado"])
        self.channel_combo.setCurrentText(self.current_channel)
        self.channel_combo.currentTextChanged.connect(self.change_channel)
        vis_layout.addWidget(self.channel_combo)
        
        vis_layout.addWidget(QtWidgets.QLabel("Ventana temporal (s):"))
        self.window_spin = QtWidgets.QSpinBox()
        self.window_spin.setRange(1, 60)
        self.window_spin.setValue(self.window_size)
        self.window_spin.valueChanged.connect(self.change_window_size)
        vis_layout.addWidget(self.window_spin)
        
        self.pause_display_btn = QtWidgets.QPushButton("Pausar Grafico")
        self.pause_display_btn.clicked.connect(self.toggle_pause_display)
        vis_layout.addWidget(self.pause_display_btn)
        
        layout.addWidget(vis_group)
        
        # === Seccion de Filtros ===
        filter_group = QtWidgets.QGroupBox("Filtros Digitales")
        filter_layout = QtWidgets.QVBoxLayout(filter_group)
        
        self.filter_check = QtWidgets.QCheckBox("Habilitar filtro adicional")
        self.filter_check.toggled.connect(self.toggle_filter)
        filter_layout.addWidget(self.filter_check)
        
        filter_layout.addWidget(QtWidgets.QLabel("Frecuencia baja (Hz):"))
        self.lowcut_spin = QtWidgets.QDoubleSpinBox()
        self.lowcut_spin.setRange(0.1, 50.0)
        self.lowcut_spin.setValue(self.filter_lowcut)
        self.lowcut_spin.setSingleStep(0.1)
        filter_layout.addWidget(self.lowcut_spin)
        
        filter_layout.addWidget(QtWidgets.QLabel("Frecuencia alta (Hz):"))
        self.highcut_spin = QtWidgets.QDoubleSpinBox()
        self.highcut_spin.setRange(1.0, 100.0)
        self.highcut_spin.setValue(self.filter_highcut)
        self.highcut_spin.setSingleStep(0.1)
        filter_layout.addWidget(self.highcut_spin)
        
        self.apply_filter_btn = QtWidgets.QPushButton("Aplicar Filtro")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.apply_filter_btn.setEnabled(False)
        filter_layout.addWidget(self.apply_filter_btn)
        
        layout.addWidget(filter_group)
        
        # === Seccion de Analisis ===
        analysis_group = QtWidgets.QGroupBox("Analisis")
        analysis_layout = QtWidgets.QVBoxLayout(analysis_group)
        
       # self.amplitude_label = QtWidgets.QLabel("Amplitud: 0")
        self.frequency_label = QtWidgets.QLabel("BEAP: 0 BPM")
       # self.peaks_label = QtWidgets.QLabel("Picos detectados: 0")
        
     #   analysis_layout.addWidget(self.amplitude_label)
        analysis_layout.addWidget(self.frequency_label)
     #   analysis_layout.addWidget(self.peaks_label)
        
        self.analyze_btn = QtWidgets.QPushButton("Analizar Señal Visible")
        self.analyze_btn.clicked.connect(self.analyze_signal)
        analysis_layout.addWidget(self.analyze_btn)
        
        layout.addWidget(analysis_group)
        
        # === Seccion de Gestion de Datos ===
        data_group = QtWidgets.QGroupBox("Gestion de Datos")
        data_layout = QtWidgets.QVBoxLayout(data_group)
        
        self.import_btn = QtWidgets.QPushButton("Importar CSV")
        self.import_btn.clicked.connect(self.import_csv)
        
        self.export_btn = QtWidgets.QPushButton("Exportar CSV")
        self.export_btn.clicked.connect(self.export_csv)
        
        data_layout.addWidget(self.import_btn)
        data_layout.addWidget(self.export_btn)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
        
        # Asignar el widget al scroll area
        scroll_area.setWidget(panel)
        return scroll_area
    
    def create_plot_panel(self):
        """Crear panel de graficos"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        
        # Widget de graficos
        
        self.plot_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.plot_widget)
        
        # Grafico principal
        self.main_plot = self.plot_widget.addPlot(title="Señal PPG")
        self.main_plot.showGrid(x=True, y=True)
        self.main_plot.setLabel('left', 'Amplitud')
        self.main_plot.setLabel('bottom', 'Tiempo (s)')
        
        # Curvas para cada canal
        self.curves = {
            'crudo': self.main_plot.plot(pen=pg.mkPen(color=(100, 100, 255), width=2), name="Crudo"),
            'filtrado': self.main_plot.plot(pen=pg.mkPen(color=(255, 100, 100), width=2), name="Filtrado"),
            'normalizado': self.main_plot.plot(pen=pg.mkPen(color=(100, 255, 100), width=2), name="Normalizado")
        }
        
        # Ocultar todas las curvas excepto la seleccionada
        self.update_visible_curves()
        
        return panel
    
    def setup_timer(self):
        """Configurar timer para actualizacion"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(1000 / FS))  # Actualizar segun la frecuencia de muestreo
    
    def connect_serial(self):
        """Conectar al puerto serie"""
        port = self.port_combo.currentText()
        
        # Crear una instancia temporal solo para probar la conexion
        test_reader = SerialReader(port, BAUD)
        
        if test_reader.connect():
            self.status_label.setText("Conectado")
            self.status_label.setStyleSheet("color: green")
            self.connect_btn.setText("Desconectar")
            self.start_btn.setEnabled(True)
            # Cerrar la conexion de prueba
            test_reader.stop_acquisition()
        else:
            self.status_label.setText("Error de conexion")
            self.status_label.setStyleSheet("color: red")
    
    def start_acquisition(self):
        """Iniciar adquisicion de datos"""
        # Detener cualquier adquisicion anterior
        if self.serial_reader is not None:
            try:
                self.serial_reader.stop_acquisition()
                # Dar tiempo para que termine el hilo anterior
                time.sleep(0.2)
            except Exception as e:
                print(f"Error deteniendo adquisicion anterior: {e}")
            finally:
                self.serial_reader = None

        # Crear una nueva instancia del SerialReader
        port = self.port_combo.currentText()
        self.serial_reader = SerialReader(port, BAUD)     
        
        # Intentar conectar
        if not self.serial_reader.connect():
            QtWidgets.QMessageBox.warning(self, "Error", "No se pudo conectar al puerto serie")
            self.serial_reader = None
            return
        
        # Establecer timestamp de inicio
        self.start_timestamp = time.time()
        
        # Limpiar datos anteriores
        self.clear_data()
        
        # Iniciar adquisicion
        self.serial_reader.start_acquisition()
        
        # Actualizar botones
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.apply_filter_btn.setEnabled(True)
    
    def pause_acquisition(self):
        """Pausar/reanudar adquisicion"""
        if self.serial_reader is None:
            return
            
        if self.serial_reader.paused:
            self.serial_reader.resume_acquisition()
            self.pause_btn.setText("Pausar")
        else:
            self.serial_reader.pause_acquisition()
            self.pause_btn.setText("Reanudar")
    
    def stop_acquisition(self):
        """Detener adquisicion"""
        if self.serial_reader is not None:
            try:
                self.serial_reader.stop_acquisition()
                # Dar tiempo para que el hilo termine correctamente
                time.sleep(0.1)
            except Exception as e:
                print(f"Error deteniendo serial reader: {e}")
            finally:
                self.serial_reader = None
        
        # Actualizar interfaz
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("Pausar")
        self.apply_filter_btn.setEnabled(False)
        
        # Resetear timestamp de inicio
        self.start_timestamp = None
    
    def change_channel(self, channel):
        """Cambiar canal de visualizacion"""
        self.current_channel = channel
        self.update_visible_curves()
    
    def update_visible_curves(self):
        """Actualizar curvas visibles"""
        for name, curve in self.curves.items():
            curve.setVisible(name == self.current_channel)
    
    def change_window_size(self, size):
        """Cambiar tamaño de ventana temporal"""
        self.window_size = size
    
    def toggle_pause_display(self):
        """Pausar/reanudar visualizacion del grafico"""
        self.is_paused_display = not self.is_paused_display
        if self.is_paused_display:
            self.pause_display_btn.setText("Reanudar Grafico")
        else:
            self.pause_display_btn.setText("Pausar Grafico")
    
    def toggle_filter(self, enabled):
        """Habilitar/deshabilitar filtro adicional"""
        self.filter_enabled = enabled
    
    def apply_filter(self):
        """Aplicar filtro a los datos"""
        if len(self.data_filtrado) < FS:  # Necesitamos al menos 1 segundo de datos
            return
        
        self.filter_lowcut = self.lowcut_spin.value()
        self.filter_highcut = self.highcut_spin.value()
        
        # Aplicar filtro a los datos filtrados existentes
        data_array = np.array(list(self.data_filtrado))
        try:
            filtered_data = filterPassBand(data_array, self.filter_lowcut, self.filter_highcut, FS, self.filter_order)
            # Actualizar el buffer de datos filtrados
            self.data_filtrado.clear()
            for val in filtered_data:
                self.data_filtrado.append(val)
        except Exception as e:
            print(f"Error aplicando filtro: {e}")
    
    def analyze_signal(self):
        """Analizar la señal visible"""
        if not self.data_filtrado:
            return
        
        # Obtener datos de la ventana visible
        window_samples = int(self.window_size * FS)
        visible_data = list(self.data_filtrado)[-window_samples:] if len(self.data_filtrado) > window_samples else list(self.data_filtrado)
        
        if len(visible_data) < 10:
            return
        
        data_array = np.array(visible_data)
        
        # Calcular parametros
        #amplitude = self.analyzer.calculate_amplitude(data_array)
        frequency = self.analyzer.calculate_frequency(data_array, FS)
        #peaks = self.analyzer.detect_peaks(data_array)
        
        # Actualizar labels
       # self.amplitude_label.setText(f"Amplitud: {amplitude:.2f}")
        self.frequency_label.setText(f"BEAP: {frequency:.1f} BPM")
       # self.peaks_label.setText(f"Picos detectados: {len(peaks)}")
    
    def import_csv(self):
        """Importar datos desde CSV"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Importar archivo CSV", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                self.clear_data()
                with open(file_path, 'r') as file:
                    reader = csv.DictReader(file)
                    first_timestamp = None
                    
                    for row in reader:
                        ts = float(row.get('timestamp', time.time()))
                        crudo = float(row.get('Crudo', 0))
                        filtrado = float(row.get('Filtrado', 0))
                        normalizado = float(row.get('Normalizado', 0))
                        
                        # Convertir a tiempo relativo desde el primer timestamp del archivo
                        if first_timestamp is None:
                            first_timestamp = ts
                            relative_time = 0
                        else:
                            relative_time = ts - first_timestamp
                        
                        self.time_data.append(relative_time)
                        self.data_crudo.append(crudo)
                        self.data_filtrado.append(filtrado)
                        self.data_normalizado.append(normalizado)                
                        print(f"Datos importados: {len(self.time_data)} muestras")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Error importando archivo: {e}")
    
    def export_csv(self):
        """Exportar datos a CSV"""
        if not self.time_data:
            QtWidgets.QMessageBox.information(self, "Informacion", "No hay datos para exportar")
            return
        
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Exportar archivo CSV", f"ppg_data_{int(time.time())}.csv", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['tiempo_relativo_s', 'Crudo', 'Filtrado', 'Normalizado'])
                    
                    for i in range(len(self.time_data)):
                        writer.writerow([
                            self.time_data[i],
                            self.data_crudo[i],
                            self.data_filtrado[i],
                            self.data_normalizado[i]
                        ])
                
                QtWidgets.QMessageBox.information(self, "exito", f"Datos exportados a {file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Error exportando archivo: {e}")
    
    def clear_data(self):
        """Limpiar todos los buffers de datos"""
        self.data_crudo.clear()
        self.data_filtrado.clear()
        self.data_normalizado.clear()
        self.time_data.clear()
    
    def update_plot(self):
        """Actualizar graficos"""
        if self.is_paused_display or self.serial_reader is None:
            return
        
        # Obtener nuevos datos
        new_data = self.serial_reader.get_data()
        
        if new_data:
            for ts, crudo, filtrado, normalizado in new_data:
                # Convertir timestamp a tiempo relativo desde el inicio
                if self.start_timestamp is not None:
                    relative_time = ts - self.start_timestamp
                else:
                    relative_time = 0
                
                self.time_data.append(relative_time)
                self.data_crudo.append(crudo)
                self.data_filtrado.append(filtrado)
                self.data_normalizado.append(normalizado)
        
        if len(self.time_data) < 2:
            return
        
        # Calcular ventana temporal
        window_samples = int(self.window_size * FS)
        
        # Obtener datos de la ventana
        if len(self.time_data) > window_samples:
            time_window = list(self.time_data)[-window_samples:]
            crudo_window = list(self.data_crudo)[-window_samples:]
            filtrado_window = list(self.data_filtrado)[-window_samples:]
            normalizado_window = list(self.data_normalizado)[-window_samples:]
        else:
            time_window = list(self.time_data)
            crudo_window = list(self.data_crudo)
            filtrado_window = list(self.data_filtrado)
            normalizado_window = list(self.data_normalizado)
        
        # Usar el tiempo relativo directamente (ya esta calculado desde el inicio)
        if time_window:
            # Actualizar curvas con el tiempo relativo
            self.curves['crudo'].setData(time_window, crudo_window)
            self.curves['filtrado'].setData(time_window, filtrado_window)
            self.curves['normalizado'].setData(time_window, normalizado_window)
    
            # Ajustar rango X para mostrar la ventana deslizante
            if len(time_window) > 0:
                t_max = max(time_window)
                t_min = max(0, t_max - self.window_size)
                self.main_plot.setXRange(t_min, t_max)
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicacion"""
        if self.serial_reader is not None:
            try:
                self.serial_reader.stop_acquisition()
                time.sleep(0.2)  # Dar tiempo para que termine el hilo
            except Exception as e:
                print(f"Error cerrando serial reader: {e}")
            finally:
                self.serial_reader = None
        event.accept()

def main():
    """Funcion principal"""
    app = QtWidgets.QApplication(sys.argv)
    
    # Establecer estilo
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()