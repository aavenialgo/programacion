import sys
import os
import time
import pandas as pd
import numpy as np
import pyqtgraph as pg
import serial
import threading
import re
from scipy.signal import find_peaks, savgol_filter, butter, filtfilt

# Importaciones de PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QSplitter, QStatusBar, QTabWidget,
    QLabel, QFileDialog, QSizePolicy, QScrollArea, QTableWidget,
    QTableWidgetItem, QMessageBox, QComboBox
)
from PyQt5.QtCore import (
    QTimer, QRunnable, QThreadPool, pyqtSignal, QObject, Qt, QSize
)
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg

# --- Configuraciones de PyQTGraph y Estilo ---
pg.setConfigOption('background', '#FFFFFF') # Fondo blanco para los gráficos
pg.setConfigOption('foreground', '#333333') # Eje y texto gris oscuro
pg.setConfigOption('leftButtonPan', False) # Deshabilita arrastrar para mover

# --- Clases de Lógica y Modelo ---

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
        self.paused = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception as e:
                print(f"Error cerrando puerto serie: {e}")
        
        if self.is_alive():
            try:
                self.join(timeout=2.0)
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

class PPGProcessor:
    """Clase para manejar el procesamiento, análisis y cálculo de parámetros PPG."""
    
    def __init__(self):
        # Datos de simulación para el puerto serie
        self.t_base = 0.0
        self.fs = 125.0 # Frecuencia de muestreo real del sensor
        self.time = np.array([])
        self.raw = np.array([])
        self.filtered = np.array([])
        self.normalized = np.array([])
        self.current_index = 0
        self.is_simulation = True  # Flag para alternar entre simulación y datos reales
        self.serial_reader = None
        self.start_timestamp = None
        
    def connect_serial(self, port, baudrate):
        """Conecta al puerto serial real."""
        try:
            # Detener cualquier conexión anterior
            if self.serial_reader is not None:
                self.serial_reader.stop_acquisition()
                time.sleep(0.2)
                
            self.serial_reader = SerialReader(port, baudrate)
            if self.serial_reader.connect():
                self.is_simulation = False
                self.start_timestamp = time.time()
                return True
            else:
                return False
        except Exception as e:
            print(f"Error conectando serial: {e}")
            return False
    
    def start_real_acquisition(self):
        """Inicia la adquisición de datos reales."""
        if self.serial_reader is not None:
            self.serial_reader.start_acquisition()
            self.start_timestamp = time.time()
    
    def pause_real_acquisition(self):
        """Pausa la adquisición de datos reales."""
        if self.serial_reader is not None:
            self.serial_reader.pause_acquisition()
    
    def stop_real_acquisition(self):
        """Detiene la adquisición de datos reales."""
        if self.serial_reader is not None:
            self.serial_reader.stop_acquisition()
            self.serial_reader = None
        self.is_simulation = True
    
    def get_real_data(self):
        """Obtiene datos reales del puerto serial."""
        if self.serial_reader is None:
            return [], [], [], []
            
        new_data = self.serial_reader.get_data()
        if not new_data:
            return [], [], [], []
        
        t_new = []
        raw_new = []
        filtered_new = []
        normalized_new = []
        
        for ts, crudo, filtrado, normalizado in new_data:
            # Convertir timestamp a tiempo relativo desde el inicio
            relative_time = ts - self.start_timestamp if self.start_timestamp else 0
            t_new.append(relative_time)
            raw_new.append(crudo)
            filtered_new.append(filtrado)
            normalized_new.append(normalizado)
        
        return np.array(t_new), np.array(raw_new), np.array(filtered_new), np.array(normalized_new)

    def generate_dummy_data(self, num_points):
        """Genera datos de PPG simulados con componentes para Crudo, Filtrado y Normalizado."""
        
        t = np.arange(self.t_base, self.t_base + num_points / self.fs, 1 / self.fs)
        
        # Simulación de señal PPG con ruido y muesca dicrotica (complejo de sin/cos)
        ppg_base = 0.5 + 0.5 * np.sin(2 * np.pi * 1.2 * t) + 0.1 * np.cos(2 * np.pi * 6 * t)
        noise = 0.05 * np.random.randn(len(t))
        raw_signal = (ppg_base + noise) * 100000 - 60000 # Escala similar a un sensor real
        
        # Simulación de filtrado (usando un suavizado simple para este ejemplo)
        filtered_signal = savgol_filter(raw_signal, window_length=15, polyorder=3)
        
        # Simulación de normalización
        min_val = np.min(filtered_signal)
        max_val = np.max(filtered_signal)
        normalized_signal = (filtered_signal - min_val) / (max_val - min_val)
        
        # Actualizar el tiempo base para la próxima generación
        self.t_base = t[-1] + 1 / self.fs
        
        return t, raw_signal, filtered_signal, normalized_signal

    def update_data(self, t, raw, filtered, normalized):
        """Añade nuevos datos a los arrays internos."""
        self.time = np.append(self.time, t)
        self.raw = np.append(self.raw, raw)
        self.filtered = np.append(self.filtered, filtered)
        self.normalized = np.append(self.normalized, normalized)

    def load_csv(self, filepath):
        """Carga datos desde un archivo CSV."""
        try:
            # Columnas esperadas: tiempo_relativo_s,Crudo,Filtrado,Normalizado
            df = pd.read_csv(filepath)
            
            self.time = df['tiempo_relativo_s'].values
            self.raw = df['Crudo'].values
            self.filtered = df['Filtrado'].values
            self.normalized = df['Normalizado'].values
            
            # Recalcular la frecuencia de muestreo (FS)
            if len(self.time) > 1:
                self.fs = 1.0 / np.mean(np.diff(self.time))
            
            return True
        except Exception as e:
            print(f"Error al cargar CSV: {e}")
            return False

    def calculate_derivatives(self, data):
        """Calcula la primera y segunda derivada usando diferencias centrales."""
        if len(data) < 3:
            return np.array([]), np.array([])
        
        dt = 1.0 / self.fs
        
        # Primera derivada (método de diferencias centrales)
        d1_dt = np.gradient(data, dt)
        
        # Segunda derivada
        d2_dt2 = np.gradient(d1_dt, dt)
        
        return d1_dt, d2_dt2

    def analyze_segment(self, t_segment, ppg_segment):
        """Realiza el análisis morfológico de la ventana seleccionada."""
        
        if len(ppg_segment) < 100:
            return None, {} # No hay suficientes datos para el análisis
        
        # 1. Suavizado y Derivadas
        # Usamos un filtro Savitzky-Golay para suavizar antes de la derivación
        # Esto es crucial para obtener derivadas limpias de la señal PPG.
        try:
            ppg_smooth = savgol_filter(ppg_segment, window_length=int(self.fs/5)+1, polyorder=3)
        except:
            # Fallback si la ventana es muy pequeña
            ppg_smooth = ppg_segment 
            
        d1, d2 = self.calculate_derivatives(ppg_smooth)
        
        # Asegurar que el tiempo de los derivados coincida con el tiempo de la señal original (mismo tamaño)
        t_aligned = t_segment
        
        # 2. Detección de Picos Fiduciales (en la señal principal)
        
        # Picos sistólicos (Systolic Peak)
        # Usamos la primera derivada para encontrar el punto de inflexión donde la pendiente es 0 después del ascenso
        peaks, _ = find_peaks(ppg_smooth, height=np.mean(ppg_smooth), distance=int(self.fs/2))
        if not list(peaks):
            peaks, _ = find_peaks(ppg_smooth, distance=int(self.fs/2)) # Intento más simple
        
        systolic_peak_idx = peaks # Posiciones de los picos sistólicos
        
        # Muesca Dicrotica (Dicrotic Notch)
        # Buscar el valle después de cada pico sistólico
        dicrotic_notch_idx = []
        for p_idx in systolic_peak_idx:
            # Buscar el mínimo en una ventana posterior al pico (e.g., 0.1s a 0.5s después del pico)
            search_start = min(p_idx + int(self.fs * 0.1), len(ppg_smooth) - 1)
            search_end = min(p_idx + int(self.fs * 0.5), len(ppg_smooth))
            
            if search_start < search_end:
                valley_idx_local = np.argmin(ppg_smooth[search_start:search_end])
                dicrotic_notch_idx.append(search_start + valley_idx_local)
        
        # 3. Detección de Puntos Fiduciales de Segunda Derivada (a, b, c, d, e)
        # Estos puntos corresponden a máximos y mínimos de la segunda derivada (d2)
        # Se asume una morfología típica 'a, b, c, d, e' por ciclo
        
        # En la práctica real, esto requeriría segmentación de ciclos
        # Para esta simulación, solo encontramos los picos y valles de d2
        d2_peaks, _ = find_peaks(d2, distance=int(self.fs / 4)) # Máximos (a, c, e)
        d2_valleys, _ = find_peaks(-d2, distance=int(self.fs / 4)) # Mínimos (b, d)
        
        fiducial_points = {
            'systolic_peak': t_aligned[systolic_peak_idx],
            'dicrotic_notch': t_aligned[dicrotic_notch_idx],
            # Para la simulación, solo tomamos el primer ciclo para los puntos de la segunda derivada
            'd2_a': t_aligned[d2_peaks[0]] if len(d2_peaks) > 0 else None,
            'd2_b': t_aligned[d2_valleys[0]] if len(d2_valleys) > 0 else None,
            'd2_c': t_aligned[d2_peaks[1]] if len(d2_peaks) > 1 else None,
            'd2_d': t_aligned[d2_valleys[1]] if len(d2_valleys) > 1 else None,
            'd2_e': t_aligned[d2_peaks[2]] if len(d2_peaks) > 2 else None,
        }
        
        # 4. Cálculo de Parámetros
        
        # Frecuencia Cardíaca (FC) e Intervalo Pulso a Pulso (PPI)
        if len(systolic_peak_idx) > 1:
            ppi_samples = np.diff(systolic_peak_idx)
            ppi_seconds = ppi_samples / self.fs
            avg_ppi = np.mean(ppi_seconds)
            fc = 60 / avg_ppi # latidos por minuto (LPM)
        else:
            fc = np.nan
            avg_ppi = np.nan

        # Amplitud Pico a Valle (AC) y Componente DC (DC)
        ac = np.max(ppg_segment) - np.min(ppg_segment)
        dc = np.mean(ppg_segment)
        
        # Tiempo de Subida (RT - Rise Time) y Relación Sistólico/Diastólico (ST/DT)
        # Simplificación: RT es el tiempo desde el valle hasta el pico sistólico
        # ST/DT: El tiempo desde el pico sistólico hasta la muesca dicrotica / El tiempo restante
        rt = np.nan
        st_dt_ratio = np.nan
        
        if len(systolic_peak_idx) > 0 and len(dicrotic_notch_idx) > 0:
            # Tomamos el primer ciclo
            pico_idx = systolic_peak_idx[0]
            valle_idx = np.argmin(ppg_segment[:pico_idx]) # Valle anterior al pico
            notch_idx = dicrotic_notch_idx[0]
            
            rt = (t_aligned[pico_idx] - t_aligned[valle_idx]) if valle_idx < pico_idx else np.nan
            
            systolic_time = t_aligned[notch_idx] - t_aligned[pico_idx]
            diastolic_time = (t_aligned[-1] - t_aligned[notch_idx]) if len(t_aligned) > 1 else np.nan
            
            if not np.isnan(systolic_time) and not np.isnan(diastolic_time) and diastolic_time > 0:
                st_dt_ratio = systolic_time / diastolic_time

        # Índices de Rigidez (Ratios b/a, c/a, d/a, e/a)
        # Estos se basan en las amplitudes de los picos de la segunda derivada.
        a = ppg_smooth[d2_peaks[0]] if len(d2_peaks) > 0 else np.nan
        b = ppg_smooth[d2_valleys[0]] if len(d2_valleys) > 0 else np.nan
        c = ppg_smooth[d2_peaks[1]] if len(d2_peaks) > 1 else np.nan
        d = ppg_smooth[d2_valleys[1]] if len(d2_valleys) > 1 else np.nan
        e = ppg_smooth[d2_peaks[2]] if len(d2_peaks) > 2 else np.nan
        
        ai = np.nan # Índice de Aumento (Augmentation Index) - Placeholder
        # Se calcula con la señal normalizada o filtrada: AI = (Amplitud pico tardío - Amplitud pico temprano) / Amplitud pulso
        # Aquí lo simplificaremos como un proxy de la onda dicrotica
        if len(dicrotic_notch_idx) > 0:
            ai = ppg_smooth[dicrotic_notch_idx[0]] / ppg_smooth[systolic_peak_idx[0]]
            
        parameters = {
            'FC (LPM)': f'{fc:.2f}' if not np.isnan(fc) else 'N/A',
            'PPI (s)': f'{avg_ppi:.3f}' if not np.isnan(avg_ppi) else 'N/A',
            'AC (Unidades)': f'{ac:.2f}',
            'DC (Unidades)': f'{dc:.2f}',
            'AI (Proxy)': f'{ai:.3f}' if not np.isnan(ai) else 'N/A',
            'RT (ms)': f'{rt * 1000:.1f}' if not np.isnan(rt) else 'N/A',
            'ST/DT': f'{st_dt_ratio:.2f}' if not np.isnan(st_dt_ratio) else 'N/A',
            'Ratio b/a': f'{(b/a):.2f}' if not np.isnan(a) and not np.isnan(b) and a != 0 else 'N/A',
            'Ratio c/a': f'{(c/a):.2f}' if not np.isnan(a) and not np.isnan(c) and a != 0 else 'N/A',
            'Ratio d/a': f'{(d/a):.2f}' if not np.isnan(a) and not np.isnan(d) and a != 0 else 'N/A',
            'Ratio e/a': f'{(e/a):.2f}' if not np.isnan(a) and not np.isnan(e) and a != 0 else 'N/A',
        }

        analysis_data = {
            'time': t_aligned,
            'ppg': ppg_segment,
            'ppg_smooth': ppg_smooth,
            'd1': d1,
            'd2': d2,
            'fiducials': fiducial_points,
            'parameters': parameters
        }
        
        return analysis_data, parameters

class AnalysisTab(QWidget):
    """Pestaña dedicada a la visualización y reporte de una ventana PPG seleccionada."""
    
    def __init__(self, data_packet, parent=None):
        super().__init__(parent)
        self.data_packet = data_packet
        self.processor = PPGProcessor()
        self.view_state = 0 # 0: PPG, 1: D1, 2: D2
        
        self.t_aligned = self.data_packet['time']
        self.ppg_segment = self.data_packet['ppg']
        self.ppg_smooth = self.data_packet['ppg_smooth']
        self.d1 = self.data_packet['d1']
        self.d2 = self.data_packet['d2']
        self.fiducials = self.data_packet['fiducials']
        self.parameters = self.data_packet['parameters']
        
        self.setup_ui()
        self.update_plot()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- 1. Panel de Gráfico (Izquierda) ---
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        
        # Título y Selector de Vista
        title_bar = QHBoxLayout()
        self.plot_title = QLabel("Ventana de Análisis: Señal PPG Cruda Suavizada")
        self.plot_title.setFont(QFont("Inter", 14, QFont.Bold))
        
        self.view_selector = QComboBox()
        self.view_selector.addItems(["Señal PPG original", "Primera derivada", "Segunda derivada"])
        self.view_selector.currentIndexChanged.connect(self.change_view)
        self.view_selector.setStyleSheet("""
            QComboBox {
                padding: 5px; 
                border-radius: 5px; 
                border: 1px solid #CCCCCC;
            }
        """)
        
        title_bar.addWidget(self.plot_title)
        title_bar.addStretch()
        title_bar.addWidget(QLabel("Vista:"))
        title_bar.addWidget(self.view_selector)
        
        plot_layout.addLayout(title_bar)
        
        # Gráfico principal
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Amplitud')
        self.plot_widget.setLabel('bottom', 'Tiempo (s)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen(color='#3B82F6', width=2))
        
        # Scatter para puntos fiduciales
        self.fiducial_scatter = pg.ScatterPlotItem(symbol='o', size=10, pen=pg.mkPen(None), brush=pg.mkBrush('#EF4444'))
        self.plot_widget.addItem(self.fiducial_scatter)

        plot_layout.addWidget(self.plot_widget)
        main_layout.addWidget(plot_container, 3) # 3/5 del ancho

        # --- 2. Panel Lateral (Derecha) ---
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(350)
        sidebar_widget.setStyleSheet("""
            QWidget {
                background-color: #F7F7F9; 
                border-radius: 12px; 
                padding: 15px;
            }
            QLabel {
                font-family: 'Inter';
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # Etiqueta de Título
        label_title = QLabel("Resultados de Análisis Morfológico")
        label_title.setFont(QFont("Inter", 12, QFont.Bold))
        sidebar_layout.addWidget(label_title)
        
        # Tabla de Parámetros
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(2)
        self.param_table.setHorizontalHeaderLabels(['Parámetro', 'Valor'])
        self.param_table.horizontalHeader().setStretchLastSection(True)
        self.param_table.verticalHeader().setVisible(False)
        
        self.update_parameters_table()
        sidebar_layout.addWidget(self.param_table)
        
        # Botón Guardar
        self.save_button = QPushButton("Guardar Resultados (.csv)")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981; 
                color: white; 
                padding: 10px; 
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.save_button.clicked.connect(self.save_analysis_data)
        sidebar_layout.addWidget(self.save_button)
        
        sidebar_layout.addStretch(1)
        main_layout.addWidget(sidebar_widget, 2) # 2/5 del ancho
        
    def update_parameters_table(self):
        """Llena la tabla con los parámetros calculados."""
        self.param_table.setRowCount(len(self.parameters))
        
        for i, (key, value) in enumerate(self.parameters.items()):
            item_key = QTableWidgetItem(key)
            item_value = QTableWidgetItem(str(value))
            
            self.param_table.setItem(i, 0, item_key)
            self.param_table.setItem(i, 1, item_value)

    def change_view(self, index):
        """Cambia entre la señal PPG, Primera Derivada y Segunda Derivada."""
        self.view_state = index
        self.update_plot()

    def update_plot(self):
        """Actualiza el gráfico basado en el estado de la vista (PPG, D1 o D2)."""
        self.plot_widget.clear()
        
        # Datos base y etiquetas
        t = self.t_aligned
        y_data = None
        fiducials_t = []
        fiducials_y = []
        y_label = 'Amplitud'
        
        if self.view_state == 0:
            y_data = self.ppg_smooth
            y_label = 'Amplitud PPG Suavizada (Unidades)'
            self.plot_title.setText("Ventana de Análisis: Señal PPG Cruda Suavizada")
            # Puntos fiduciales para PPG: Pico Sistólico y Muesca Dicrotica
            for t_val in self.fiducials['systolic_peak']:
                if t_val is not None: fiducials_t.append(t_val)
            for t_val in self.fiducials['dicrotic_notch']:
                if t_val is not None: fiducials_t.append(t_val)
            
            # Coordenadas Y para los puntos fiduciales en PPG
            for t_val in fiducials_t:
                idx = np.argmin(np.abs(t - t_val))
                fiducials_y.append(y_data[idx])

        elif self.view_state == 1:
            y_data = self.d1
            y_label = 'Primera Derivada (dPPG/dt)'
            self.plot_title.setText("Ventana de Análisis: Primera Derivada (dPPG)")
            # Puntos fiduciales para D1: Picos que marcan la velocidad
            # Usualmente se usan el Pico A (ascenso) y Pico B (descenso)
            
        elif self.view_state == 2:
            y_data = self.d2
            y_label = 'Segunda Derivada (d²PPG/dt²)'
            self.plot_title.setText("Ventana de Análisis: Segunda Derivada (d²PPG)")
            # Puntos fiduciales para D2: a, b, c, d, e
            d2_points = ['d2_a', 'd2_b', 'd2_c', 'd2_d', 'd2_e']
            
            for key in d2_points:
                t_val = self.fiducials.get(key)
                if t_val is not None: fiducials_t.append(t_val)
            
            # Coordenadas Y para los puntos fiduciales en D2
            for t_val in fiducials_t:
                idx = np.argmin(np.abs(t - t_val))
                fiducials_y.append(y_data[idx])
        
        
        # Ploteo de la señal
        self.plot_curve = self.plot_widget.plot(t, y_data, 
                                                pen=pg.mkPen(color='#3B82F6', width=2))
        self.plot_widget.setLabel('left', y_label)
        
        # Ploteo de los puntos fiduciales
        if fiducials_t:
            # Recrear el ScatterPlotItem para los nuevos datos
            self.fiducial_scatter = pg.ScatterPlotItem(
                x=fiducials_t, 
                y=fiducials_y, 
                symbol='o', 
                size=10, 
                pen=pg.mkPen(None), 
                brush=pg.mkBrush('#EF4444')
            )
            self.plot_widget.addItem(self.fiducial_scatter)

    def save_analysis_data(self):
        """Guarda la ventana analizada y los parámetros en un archivo CSV."""
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Resultados de Análisis", 
                                                "analisis_ppg.csv", 
                                                "CSV Files (*.csv)")
        if path:
            try:
                # 1. Crear DataFrame con la señal, d1 y d2
                df_signal = pd.DataFrame({
                    'Tiempo (s)': self.t_aligned,
                    'PPG Suavizada': self.ppg_smooth,
                    'Primera Derivada': self.d1,
                    'Segunda Derivada': self.d2,
                })
                
                # 2. Crear DataFrame con los parámetros
                df_params = pd.DataFrame(self.parameters.items(), columns=['Parámetro', 'Valor'])
                
                # Guardar señal y derivadas (con delimitador que no cause conflicto)
                df_signal.to_csv(path, index=False)
                
                # Adjuntar parámetros al mismo archivo CSV, separados por una línea
                with open(path, 'a') as f:
                    f.write('\n\n--- Parámetros Calculados ---\n')
                    df_params.to_csv(f, index=False, header=True)
                    
                QMessageBox.information(self, "Éxito", f"Datos de análisis guardados exitosamente en:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo: {e}")

# Muestra visual de los puntos fiduciales de PPG
# 

class AcquisitionTab(QWidget):
    """Pestaña principal para la adquisición de datos y visualización en tiempo real."""
    
    def __init__(self, processor, parent=None):
        super().__init__(parent)
        self.processor = processor
        self.is_paused = False
        self.serial_connected = False
        self.default_window_s = 5.0 # Duración por defecto para el ROI
        self.current_channel = "crudo"  # Canal por defecto para visualización
        
        self.setup_ui()
        self.init_timer()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- 1. Indicadores Superiores ---
        indicator_style = "QLabel { font-weight: bold; padding: 5px; border-radius: 6px; color: white; }"
        
        self.status_label = QLabel("DESCONECTADO")
        self.status_label.setStyleSheet(indicator_style + "background-color: #EF4444;")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel("Tiempo Transcurrido: 0.00 s")
        self.time_label.setStyleSheet(indicator_style + "background-color: #3B82F6;")
        self.time_label.setAlignment(Qt.AlignCenter)
        
        self.window_label = QLabel(f"Ventana de Análisis: {self.default_window_s:.1f} s")
        self.window_label.setStyleSheet(indicator_style + "background-color: #10B981;")
        self.window_label.setAlignment(Qt.AlignCenter)

        indicators_layout = QHBoxLayout()
        indicators_layout.addWidget(self.status_label, 1)
        indicators_layout.addWidget(self.time_label, 1)
        indicators_layout.addWidget(self.window_label, 1)
        
        main_layout.addLayout(indicators_layout)

        # --- 2. Selector de Canal ---
        channel_layout = QHBoxLayout()
        channel_label = QLabel("Canal a visualizar:")
        channel_label.setFont(QFont("Inter", 10, QFont.Bold))
        
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["crudo", "filtrado", "normalizado"])
        self.channel_combo.setCurrentText(self.current_channel)
        self.channel_combo.currentTextChanged.connect(self.change_channel)
        self.channel_combo.setStyleSheet("""
            QComboBox {
                padding: 5px; 
                border-radius: 5px; 
                border: 1px solid #CCCCCC;
                background-color: white;
            }
        """)
        
        channel_layout.addWidget(channel_label)
        channel_layout.addWidget(self.channel_combo)
        channel_layout.addStretch()
        main_layout.addLayout(channel_layout)

        # --- 3. Plot Widget ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Amplitud')
        self.plot_widget.setLabel('bottom', 'Tiempo Relativo (s)')
        self.plot_widget.setTitle("Visualización en Tiempo Real - Canal Crudo")
        self.plot_widget.showGrid(x=True, y=True)
        
        # Curvas
        self.curve_raw = self.plot_widget.plot(pen=pg.mkPen(color='#3B82F6', width=2), name='Crudo')
        self.curve_filtered = self.plot_widget.plot(pen=pg.mkPen(color='#10B981', width=1), name='Filtrado', visible=False)
        self.curve_normalized = self.plot_widget.plot(pen=pg.mkPen(color='#F59E0B', width=1), name='Normalizado', visible=False)
        
        # Región de Interés (ROI) para la selección de la ventana
        self.roi = pg.LinearRegionItem(values=[0, self.default_window_s], movable=True)
        self.roi.setBrush(QColor(60, 130, 246, 50)) # Azul claro transparente
        self.roi.setZValue(10)
        self.plot_widget.addItem(self.roi)
        
        main_layout.addWidget(self.plot_widget, 1) # Expandir
        
        # Inicializar la visibilidad de las curvas
        self.update_visible_curves()

    def change_channel(self, channel):
        """Cambiar canal de visualización"""
        self.current_channel = channel
        self.update_visible_curves()
        
        # Actualizar título del gráfico
        channel_names = {
            "crudo": "Canal Crudo",
            "filtrado": "Canal Filtrado", 
            "normalizado": "Canal Normalizado"
        }
        self.plot_widget.setTitle(f"Visualización en Tiempo Real - {channel_names[channel]}")

    def update_visible_curves(self):
        """Actualizar curvas visibles según el canal seleccionado"""
        self.curve_raw.setVisible(self.current_channel == "crudo")
        self.curve_filtered.setVisible(self.current_channel == "filtrado")
        self.curve_normalized.setVisible(self.current_channel == "normalizado")

    def init_timer(self):
        """Inicializa el temporizador para la simulación de adquisición."""
        self.timer = QTimer()
        self.timer.setInterval(50) # Actualización cada 50ms
        self.timer.timeout.connect(self.update_plot_data)
        
        # Contador de tiempo transcurrido
        self.elapsed_timer = QTimer()
        self.elapsed_timer.setInterval(100)
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)
        self.start_time = time.time()
        self.total_elapsed_time = 0.0

    def start_acquisition(self):
        """Inicia o reanuda la adquisición de datos."""
        self.is_paused = False
        self.serial_connected = True
        
        # Iniciar adquisición real si está conectado al puerto serial
        if not self.processor.is_simulation:
            self.processor.start_real_acquisition()
        
        self.status_label.setText("CONECTADO")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; border-radius: 6px; color: white; background-color: #10B981; }")
        
        self.start_time = time.time() - self.total_elapsed_time
        self.timer.start()
        self.elapsed_timer.start()

    def pause_acquisition(self):
        """Pausa la adquisición de datos."""
        self.is_paused = True
        self.timer.stop()
        self.elapsed_timer.stop()
        
        # Pausar adquisición real si está conectado al puerto serial
        if not self.processor.is_simulation:
            self.processor.pause_real_acquisition()
        
        self.total_elapsed_time = time.time() - self.start_time
        
        self.status_label.setText("PAUSADO")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; border-radius: 6px; color: white; background-color: #F59E0B; }")

    def reset_acquisition(self):
        """Reinicia la adquisición y limpia los datos."""
        self.pause_acquisition()
        
        # Detener adquisición real si está conectado
        if not self.processor.is_simulation:
            self.processor.stop_real_acquisition()
            
        self.processor.time = np.array([])
        self.processor.raw = np.array([])
        self.processor.filtered = np.array([])
        self.processor.normalized = np.array([])
        self.processor.t_base = 0.0
        
        self.curve_raw.setData([], [])
        self.curve_filtered.setData([], [])
        self.curve_normalized.setData([], [])
        
        self.total_elapsed_time = 0.0
        self.time_label.setText("Tiempo Transcurrido: 0.00 s")
        
        self.status_label.setText("DESCONECTADO")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; border-radius: 6px; color: white; background-color: #EF4444; }")


    def update_elapsed_time(self):
        """Actualiza el indicador de tiempo transcurrido."""
        if not self.is_paused:
            self.total_elapsed_time = time.time() - self.start_time
        self.time_label.setText(f"Tiempo Transcurrido: {self.total_elapsed_time:.2f} s")

    def update_plot_data(self):
        """Lee datos del puerto serie (real o simulado) y actualiza el gráfico."""
        if self.is_paused or not self.serial_connected:
            return

        # Obtener datos (reales o simulados)
        if self.processor.is_simulation:
            # Simular lectura de datos (20 puntos por actualización)
            t_new, raw_new, filtered_new, normalized_new = self.processor.generate_dummy_data(20)
        else:
            # Leer datos reales del puerto serial
            t_new, raw_new, filtered_new, normalized_new = self.processor.get_real_data()
        
        # Solo actualizar si hay datos válidos
        if len(t_new) > 0:
            self.processor.update_data(t_new, raw_new, filtered_new, normalized_new)
        
        # Obtener todos los datos
        t = self.processor.time
        raw = self.processor.raw
        
        # Limitar la ventana visible a los últimos 10 segundos
        max_visible_time = 10
        if len(t) > 0:
            t_start = max(t[-1] - max_visible_time, 0)
            
            # Recortar datos para una mejor visualización de alto rendimiento
            idx_start = np.searchsorted(t, t_start)
            t_view = t[idx_start:]
            raw_view = self.processor.raw[idx_start:]
            filtered_view = self.processor.filtered[idx_start:]
            normalized_view = self.processor.normalized[idx_start:]
            
            # Actualizar solo las curvas visibles basado en la selección actual
            self.curve_raw.setData(t_view, raw_view)
            self.curve_filtered.setData(t_view, filtered_view)
            self.curve_normalized.setData(t_view, normalized_view)

            # Reajustar el rango X
            self.plot_widget.setXRange(t_view[0], t_view[-1] if len(t_view) > 1 else t_view[0] + 1)
            
            # Ajustar la posición inicial del ROI al final de la ventana
            if len(t) > self.processor.fs * self.default_window_s:
                end_pos = t[-1]
                start_pos = end_pos - self.default_window_s
                self.roi.setRegion([start_pos, end_pos])
            else:
                self.roi.setRegion([0, self.default_window_s])

    def load_csv_file(self):
        """Abre un diálogo para cargar un archivo CSV."""
        path, _ = QFileDialog.getOpenFileName(self, "Cargar Archivo CSV de PPG", "", 
                                                "CSV Files (*.csv)")
        if path:
            self.reset_acquisition()
            if self.processor.load_csv(path):
                # La carga de CSV simula la adquisición completa
                self.serial_connected = True
                self.pause_acquisition()
                self.status_label.setText("CSV CARGADO")
                self.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; border-radius: 6px; color: white; background-color: #3B82F6; }")
                
                # Ploteo de todos los datos del CSV
                t = self.processor.time
                raw = self.processor.raw
                filtered = self.processor.filtered
                normalized = self.processor.normalized
                
                self.curve_raw.setData(t, raw)
                self.curve_filtered.setData(t, filtered)
                self.curve_normalized.setData(t, normalized)
                
                self.plot_widget.autoRange()
                
                self.total_elapsed_time = t[-1] if len(t) > 0 else 0.0
                self.time_label.setText(f"Tiempo Total: {self.total_elapsed_time:.2f} s")
                
            else:
                QMessageBox.critical(self, "Error de Carga", "El archivo CSV no pudo ser cargado o tiene un formato incorrecto.")


class PPGAnalyzerApp(QMainWindow):
    """Ventana principal de la aplicación con estilo Dashboard."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador de Señal PPG (Fotopletismografía)")
        self.setGeometry(100, 100, 1366, 768) # Adaptable a 1366x768
        
        # Inicializar el procesador de datos
        self.processor = PPGProcessor()
        
        self.setup_ui()

    def setup_ui(self):
        # --- 1. Contenedor Central ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- 2. Menú Lateral (Dashboard Style) ---
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #F7F7F9; 
                border-right: 1px solid #E5E7EB;
                border-radius: 15px; 
                margin: 5px;
            }
            QPushButton {
                background-color: #FFFFFF; 
                color: #333333; 
                text-align: left; 
                padding: 12px 15px; 
                border-radius: 8px; 
                margin: 5px 0;
                border: 1px solid #D1D5DB;
                font-family: 'Inter';
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                border: 1px solid #9CA3AF;
            }
            QPushButton#mainAction {
                background-color: #3B82F6; 
                color: white;
            }
            QPushButton#mainAction:hover {
                background-color: #2563EB;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        # Título
        title_label = QLabel("PPG Analyzer")
        title_label.setFont(QFont("Inter", 16, QFont.Bold))
        title_label.setStyleSheet("color: #1F2937;")
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(15)
        
        # Configuración de Puerto
        port_label = QLabel("Configuración:")
        port_label.setFont(QFont("Inter", 10, QFont.Bold))
        sidebar_layout.addWidget(port_label)
        
        # Configuración de Puerto Serial
        self.port_input = QLineEdit("/dev/ttyUSB0")
        self.port_input.setPlaceholderText("Puerto Serie")
        self.baud_input = QLineEdit("115200")
        self.baud_input.setPlaceholderText("BAUD Rate")
        
        self.config_button = QPushButton("Configurar Puerto / Conectar")
        self.config_button.clicked.connect(self.connect_serial)
        sidebar_layout.addWidget(self.port_input)
        sidebar_layout.addWidget(self.baud_input)
        sidebar_layout.addWidget(self.config_button)

        # Cargar CSV
        self.load_csv_button = QPushButton("Cargar Archivo CSV")
        # Conectar después de crear acquisition_tab
        sidebar_layout.addWidget(self.load_csv_button)
        sidebar_layout.addSpacing(10)
        
        # Botones de Control de Adquisición
        self.start_button = QPushButton("Iniciar adquisición")
        self.start_button.setProperty("class", "mainAction")
        # Conectar después de crear acquisition_tab
        
        self.pause_button = QPushButton("Pausar adquisición")
        # Conectar después de crear acquisition_tab
        
        self.reset_button = QPushButton("Reiniciar")
        # Conectar después de crear acquisition_tab

        sidebar_layout.addWidget(self.start_button)
        sidebar_layout.addWidget(self.pause_button)
        sidebar_layout.addWidget(self.reset_button)
        sidebar_layout.addSpacing(15)
        
        # Análisis - usar valor por defecto directamente
        self.window_input = QLineEdit("5.0")  # Usar valor por defecto
        self.window_input.setPlaceholderText("Duración Ventana (s)")
        self.window_input.textChanged.connect(self.update_window_length)
        
        self.analyze_button = QPushButton("Analizar ventana")
        self.analyze_button.setProperty("class", "mainAction")
        self.analyze_button.clicked.connect(self.open_analysis_tab)
        
        sidebar_layout.addWidget(QLabel("Ventana de Análisis (s):"))
        sidebar_layout.addWidget(self.window_input)
        sidebar_layout.addWidget(self.analyze_button)
        sidebar_layout.addSpacing(20)
        
        # Botones Finales
        self.exit_button = QPushButton("Salir")
        self.exit_button.clicked.connect(self.close)
        
        sidebar_layout.addStretch(1)
        sidebar_layout.addWidget(self.exit_button)
        
        main_layout.addWidget(sidebar)
        
        # --- 3. Área Principal de Pestañas ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { /* The tab widget frame */
                border: 0px solid #C4C4C3;
                border-radius: 15px;
                padding: 5px;
                margin-left: -5px;
            }
            QTabBar::tab {
                background: #E5E7EB;
                border: 1px solid #D1D5DB;
                border-bottom-color: #C2C7CB; /* lighter than pane color */
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 5px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                border-color: #3B82F6;
                border-bottom: 2px solid #3B82F6;
                font-weight: bold;
            }
        """)
        
        # Pestaña de Adquisición
        self.acquisition_tab = AcquisitionTab(self.processor)
        self.tab_widget.addTab(self.acquisition_tab, "Adquisición y Visualización")
        
        # Ahora conectar los botones después de crear acquisition_tab
        self.load_csv_button.clicked.connect(lambda: self.acquisition_tab.load_csv_file())
        self.start_button.clicked.connect(lambda: self.acquisition_tab.start_acquisition())
        self.pause_button.clicked.connect(lambda: self.acquisition_tab.pause_acquisition())
        self.reset_button.clicked.connect(lambda: self.acquisition_tab.reset_acquisition())
        
        main_layout.addWidget(self.tab_widget)
        
        # Inicializar el botón de ventana de análisis con la duración por defecto
        self.update_window_length(self.window_input.text())
        
    def connect_serial(self):
        """Conecta al puerto serial real."""
        port = self.port_input.text()
        baud = self.baud_input.text()
        
        try:
            baud_rate = int(baud)
        except ValueError:
            QMessageBox.warning(self, "Error", "La velocidad de baudios debe ser un número válido")
            return
        
        # Intentar conectar al puerto serial real
        if self.processor.connect_serial(port, baud_rate):
            QMessageBox.information(self, "Conexión Serial", f"Conectado exitosamente a {port}")
            self.acquisition_tab.serial_connected = True
            self.acquisition_tab.status_label.setText("CONECTADO - REAL")
            self.acquisition_tab.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; border-radius: 6px; color: white; background-color: #10B981; }")
        else:
            # Si falla la conexión real, usar modo simulación
            QMessageBox.warning(self, "Conexión Fallida", 
                               f"No se pudo conectar a {port}. Usando modo simulación.")
            self.acquisition_tab.serial_connected = True
            self.acquisition_tab.status_label.setText("MODO SIMULACIÓN")
            self.acquisition_tab.status_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; border-radius: 6px; color: white; background-color: #F59E0B; }")

    def update_window_length(self, text):
        """Actualiza la duración de la ventana de análisis y el indicador."""
        try:
            length = float(text)
            if length > 0:
                self.acquisition_tab.default_window_s = length
                self.acquisition_tab.window_label.setText(f"Ventana de Análisis: {length:.1f} s")
            else:
                raise ValueError
        except ValueError:
            # Si el input no es válido, usa el valor anterior
            self.acquisition_tab.window_label.setText(f"Ventana de Análisis: {self.acquisition_tab.default_window_s:.1f} s")
            self.window_input.setText(str(self.acquisition_tab.default_window_s))

    def open_analysis_tab(self):
        """
        Pausa la adquisición, toma el segmento de datos de la ROI y abre la pestaña de análisis.
        """
        # 1. Pausar la adquisición
        self.acquisition_tab.pause_acquisition()
        
        # 2. Obtener la región seleccionada
        region = self.acquisition_tab.roi.getRegion()
        t_start, t_end = region
        
        full_time = self.processor.time
        full_raw = self.processor.raw # Analizar el canal Crudo como se solicitó

        if len(full_time) == 0:
            QMessageBox.warning(self, "Advertencia", "No hay datos para analizar. Inicie la adquisición o cargue un CSV.")
            return
            
        # Encontrar índices de inicio y fin
        idx_start = np.searchsorted(full_time, t_start)
        idx_end = np.searchsorted(full_time, t_end)
        
        # Asegurar que el rango sea válido
        if idx_start >= idx_end:
            QMessageBox.warning(self, "Advertencia", "El rango seleccionado es inválido o demasiado pequeño.")
            return

        # Recortar datos
        t_segment = full_time[idx_start:idx_end]
        ppg_segment = full_raw[idx_start:idx_end]
        
        # 3. Realizar el análisis
        analysis_data, parameters = self.processor.analyze_segment(t_segment, ppg_segment)
        
        if analysis_data is None:
            QMessageBox.warning(self, "Advertencia", "Datos insuficientes en la ventana para realizar el análisis.")
            return

        # 4. Crear y agregar la nueva pestaña de análisis
        # Cerrar cualquier pestaña de análisis anterior para mantener la interfaz limpia
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i).startswith("Análisis"):
                self.tab_widget.removeTab(i)
                break
        
        new_analysis_tab = AnalysisTab(analysis_data)
        tab_index = self.tab_widget.addTab(new_analysis_tab, "Análisis de Ventana")
        self.tab_widget.setCurrentIndex(tab_index)
        
        QMessageBox.information(self, "Análisis Completo", 
                                "El análisis de la ventana seleccionada se ha completado. Revisar la nueva pestaña 'Análisis de Ventana'.")
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicación."""
        if self.processor.serial_reader is not None:
            try:
                self.processor.stop_real_acquisition()
                time.sleep(0.2)  # Dar tiempo para que termine el hilo
            except Exception as e:
                print(f"Error cerrando conexión serial: {e}")
        event.accept()
        
        
if __name__ == '__main__':
    # Usar el estilo "Fusion" para un aspecto moderno si está disponible
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    # Configuración de fuente legible
    font = QFont("Inter", 10)
    app.setFont(font)
    
    # Crear y mostrar la aplicación
    window = PPGAnalyzerApp()
    window.show()
    
    # Iniciar el loop de la aplicación
    sys.exit(app.exec_())