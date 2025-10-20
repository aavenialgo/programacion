import sys
import serial
import threading
import time
import csv
from collections import deque
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import re
import numpy as np
# Importar el módulo de filtros - agregar el directorio padre al path
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from filter import filterPassBand, moving_average


# source env/bin/activate

# === CONFIGURACIÓN ===
PORT = '/dev/ttyUSB0'   # 
BAUD = 115200
FS = 125                # frecuencia de muestreo (Hz)
MAX_POINTS = 3 * FS    #  segundos en pantalla
SAVE_CSV = 'sensor_data_log.csv'

# Parámetros del filtro pasabanda
LOWCUT = 0.5    # Hz - frecuencia de corte baja
HIGHCUT = 15.0  # Hz - frecuencia de corte alta
FILTER_ORDER = 4
MIN_SAMPLES_FILTER = 3 * FS  # mínimo de muestras para aplicar filtro (3 segundos)

# === LECTOR SERIE ===
class SerialReader(threading.Thread):
    def __init__(self, port, baud):
        super().__init__(daemon=True)
        self.ser = serial.Serial(port, baud, timeout=1)
        self.lock = threading.Lock()
        self.running = True
        self.buffer = []

        # Archivo CSV
        self.csvfile = open(SAVE_CSV, 'w', newline='')
        self.csvwriter = csv.writer(self.csvfile)
        self.csvwriter.writerow(['timestamp', 'Crudo', 'Filtrado', 'Normalizado'])

        # Regex para extraer los nuevos valores (Crudo:-385.00,Filtrado:15.7351,Normalizado:0.7565)
        self.pattern = re.compile(r"Crudo:(-?\d+(?:\.\d+)?),Filtrado:(-?\d+(?:\.\d+)?),Normalizado:(-?\d+(?:\.\d+)?)", re.IGNORECASE)

    def run(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors='ignore').strip()

                match = self.pattern.search(line)
                if match:
                    crudo_val = float(match.group(1))
                    filtrado_val = float(match.group(2))
                    normalizado_val = float(match.group(3))
                    
                    print(f"Crudo: {crudo_val}, Filtrado: {filtrado_val}, Normalizado: {normalizado_val}")  # Debug
                    ts = time.time()
                    with self.lock:
                        self.buffer.append((ts, crudo_val, filtrado_val, normalizado_val))
                    self.csvwriter.writerow([ts, crudo_val, filtrado_val, normalizado_val])
            except Exception as e:
                print("Error:", e)
                time.sleep(0.1)

    def get_data(self):
        with self.lock:
            data = self.buffer[:]
            self.buffer.clear()
        return data

    def stop(self):
        self.running = False
        try:
            self.ser.close()
            self.csvfile.close()
        except:
            pass

# === Interfaz ===
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, serial_reader):
        super().__init__()
        self.sr = serial_reader
        
        # Deques para cada tipo de dato
        self.data_crudo = deque(maxlen=MAX_POINTS)
        self.data_filtrado = deque(maxlen=MAX_POINTS)
        self.data_normalizado = deque(maxlen=MAX_POINTS)
        self.time_deque = deque(maxlen=MAX_POINTS)
        
        # Buffer para el filtrado adicional (si es necesario)
        self.filter_buffer_data = deque(maxlen=MAX_POINTS * 2)
        self.filter_buffer_time = deque(maxlen=MAX_POINTS * 2)
        self.additional_filtered_data = deque(maxlen=MAX_POINTS)
        
        self.init_ui()

        # Actualización según frecuencia de muestreo
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(1000 / FS))

    def init_ui(self):
        self.setWindowTitle("Monitor Serie - Datos del Sensor (Crudo, Filtrado, Normalizado)")
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        layout = QtWidgets.QVBoxLayout(cw)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)

        # Curvas para cada tipo de dato
        self.curve_crudo = self.plot_widget.plot(
            pen=pg.mkPen(color=(100, 100, 255), width=1),
            name="Crudo"
        )
        
        self.curve_filtrado = self.plot_widget.plot(
            pen=pg.mkPen(color=(255, 100, 100), width=2),
            name="Filtrado"
        )
        
        self.curve_normalizado = self.plot_widget.plot(
            pen=pg.mkPen(color=(100, 255, 100), width=2),
            name="Normalizado"
        )

    def update_plot(self):
        new_data = self.sr.get_data()
        print("lee un dato")
        if not new_data:
            return

        # Agregar nuevos datos a los buffers
        for ts, crudo, filtrado, normalizado in new_data:
            self.time_deque.append(ts)
            self.data_crudo.append(crudo)
            self.data_filtrado.append(filtrado)
            self.data_normalizado.append(normalizado)
            
            # Buffer para filtrado adicional (usando el valor filtrado)
            self.filter_buffer_time.append(ts)
            self.filter_buffer_data.append(filtrado)
            
        if len(self.time_deque) < 2:
            return
        
        # Eje de tiempo relativo
        t_last = self.time_deque[-1]
        times = [t - t_last for t in self.time_deque]
        
        # Graficar las tres señales
        self.curve_crudo.setData(times, list(self.data_crudo))
        self.curve_filtrado.setData(times, list(self.data_filtrado))
        self.curve_normalizado.setData(times, list(self.data_normalizado))
        
        # Aplicar filtro adicional si es necesario (opcional)
        if len(self.filter_buffer_data) >= MIN_SAMPLES_FILTER:
            try:
                # Convertir a numpy array para el filtrado adicional
                data_array = np.array(list(self.filter_buffer_data))
                
                # Aplicar filtro pasabanda adicional
                additional_filtered = filterPassBand(data_array, LOWCUT, HIGHCUT, FS, FILTER_ORDER)
                additional_filtered = moving_average(additional_filtered, window_size=10)
                
                # Actualizar datos con filtrado adicional (solo los últimos MAX_POINTS)
                self.additional_filtered_data.clear()
                start_idx = max(0, len(additional_filtered) - MAX_POINTS)
                for i in range(start_idx, len(additional_filtered)):
                    self.additional_filtered_data.append(additional_filtered[i])
                
                # Opcional: Agregar curva adicional para el filtro extra
                # self.curve_additional_filter.setData(times[-len(self.additional_filtered_data):], 
                #                                     list(self.additional_filtered_data))
                
            except Exception as e:
                print(f"Error en filtrado adicional: {e}")
        
        windows_seconds = 10
        self.plot_widget.setXRange(-windows_seconds, 0)  # mostrar últimos 10 seg
        
    def closeEvent(self, event):
        self.sr.stop()
        event.accept()

# === MAIN ===
def main():
    sr = SerialReader(PORT, BAUD)
    sr.start()

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(sr)
    win.resize(900, 500)
    win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()