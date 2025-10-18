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
# Importar el módulo de filtros
sys.path.append('src')
from src.filter import filterPassBand


# source env/bin/activate

# === CONFIGURACIÓN ===
PORT = '/dev/ttyUSB0'   # 
BAUD = 115200
FS = 125                # frecuencia de muestreo (Hz)
MAX_POINTS = 3 * FS    #  segundos en pantalla
SAVE_CSV = 'red_ir_log3.csv'

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
        self.csvwriter.writerow(['timestamp', 'Red', 'IR'])

        # Regex para extraer Red e IR (por ejemplo: >Red:713,IR:706)
        self.pattern = re.compile(r"Red:(\d+),IR:(\d+)", re.IGNORECASE)

    def run(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                match = self.pattern.search(line)
                if match:
                    red_val = float(match.group(1))
                    ir_val = float(match.group(2))
                    ts = time.time()
                    with self.lock:
                        self.buffer.append((ts, red_val, ir_val))
                    self.csvwriter.writerow([ts, red_val, ir_val])
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
        self.data_deques = [deque(maxlen=MAX_POINTS)]
        self.time_deque = deque(maxlen=MAX_POINTS)
        
        # Buffer para el filtrado (necesitamos más muestras para filtrar correctamente)
        self.filter_buffer_ir = deque(maxlen=MAX_POINTS * 2)
        self.filter_buffer_time = deque(maxlen=MAX_POINTS * 2)
        self.filtered_data = deque(maxlen=MAX_POINTS)
        
        self.init_ui()

        # Actualizacin segun frecuencia de muestreo
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(1000 / FS))

    def init_ui(self):
        self.setWindowTitle("Monitor Serie - Señal IR Filtrada (0.5-20 Hz)")
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        layout = QtWidgets.QVBoxLayout(cw)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)

        self.curve_ir_filtered = self.plot_widget.plot(
            pen=pg.mkPen(color=(255, 100, 100), width=2),
            name="IR Filtrada (0.5-20 Hz)"
        )

    def update_plot(self):
        new_data = self.sr.get_data()
        if not new_data:
            return

        # Agregar nuevos datos a los buffers
        for ts, red, ir in new_data:
            self.time_deque.append(ts)
            self.data_deques[0].append(ir)
            
            # Buffer para filtrado (más datos para mayor estabilidad)
            self.filter_buffer_time.append(ts)
            self.filter_buffer_ir.append(-1*ir)
            
        if len(self.time_deque) < 2:
            return
        
        # Aplicar filtro si tenemos suficientes muestras
        if len(self.filter_buffer_ir) >= MIN_SAMPLES_FILTER:

# source env/bin/activate

# === CONFIGURA
            try:
                # Convertir a numpy array para el filtrado
                ir_data = np.array(list(self.filter_buffer_ir))
                
                # Aplicar filtro pasabanda
                filtered_ir = filterPassBand(ir_data, LOWCUT, HIGHCUT, FS, FILTER_ORDER)
                
                # Actualizar datos filtrados (solo los últimos MAX_POINTS)
                self.filtered_data.clear()
                start_idx = max(0, len(filtered_ir) - MAX_POINTS)
                for i in range(start_idx, len(filtered_ir)):
                    self.filtered_data.append(filtered_ir[i])
                
                # Eje de tiempo relativo
                t_last = self.time_deque[-1]
                times = [t - t_last for t in list(self.time_deque)[-len(self.filtered_data):]]
                
                # Graficar solo la señal filtrada
                self.curve_ir_filtered.setData(times, list(self.filtered_data))
                
            except Exception as e:
                print(f"Error en filtrado: {e}")
                # Si falla el filtro, mostrar señal original
                t_last = self.time_deque[-1]
                times = [t - t_last for t in self.time_deque]
                self.curve_ir_filtered.setData(times, list(self.data_deques[0]))
        else:
            # Mostrar señal original hasta tener suficientes datos para filtrar
            t_last = self.time_deque[-1]
            times = [t - t_last for t in self.time_deque]
            self.curve_ir_filtered.setData(times, list(self.data_deques[0]))
        
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
