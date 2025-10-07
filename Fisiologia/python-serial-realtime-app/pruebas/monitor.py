import sys
import serial
import threading
import time
import csv
from collections import deque
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import re

# === CONFIGURACIÓN ===
PORT = '/dev/ttyUSB0'   # 
BAUD = 115200
FS = 125                # frecuencia de muestreo (Hz)
MAX_POINTS = 10 * FS    # ~10 segundos en pantalla
SAVE_CSV = 'red_ir_log.csv'

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
        self.data_deques = [deque(maxlen=MAX_POINTS), deque(maxlen=MAX_POINTS)]
        self.time_deque = deque(maxlen=MAX_POINTS)
        self.init_ui()

        # Actualizacin segun frecuencia de muestreo
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(1000 / FS))

    def init_ui(self):
        self.setWindowTitle("Monitor Serie - Señales Red & IR (125 Hz)")
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        layout = QtWidgets.QVBoxLayout(cw)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        layout.addWidget(self.plot_widget)

        # Dos curvas: Red y IR
        self.curve_red = self.plot_widget.plot(
            pen=pg.mkPen(color=(255, 0, 0), width=2),
            name="Red"
        )
        # self.curve_ir = self.plot_widget.plot(
        #     pen=pg.mkPen(color=(0, 200, 255), width=2),
        #     name="IR"
        # )

    def update_plot(self):
        new_data = self.sr.get_data()
        if not new_data:
            return

        for ts, red, ir in new_data:
            self.time_deque.append(ts)
            self.data_deques[0].append(red)
            # self.data_deques[1].append(ir)

        if len(self.time_deque) < 2:
            return

        # Eje de tiempo relativo
        t0 = self.time_deque[0]
        times = [t - t0 for t in self.time_deque]

        self.curve_red.setData(times, list(self.data_deques[0]))
        self.curve_ir.setData(times, list(self.data_deques[1]))

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
