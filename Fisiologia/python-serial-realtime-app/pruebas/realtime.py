import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.signal import butter, filtfilt

class realtime:
    def __init__(self):
        self.fs = 125
        self.window_sec = 5
        self.window_size = self.fs * self.window_sec
        self.serial_port = '/dev/ttyUSB0'
        self.baudrate = 115200
        self.red_values = []
        self.fig, self.ax = plt.subplots()
        self.line_raw = None
        self.line_filt = None
        self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1) #por defecto


        self.red_values = []

        self.config_plots()

    def set_configSerial(self, serial_port, baudrate):

        self.ser = serial.Serial(serial_port, baudrate, timeout=1)

    def butterworth_filter(self, data, fs, cutoff, btype='low', order=4):
        nyq = 0.5 * fs
        normal_cutoff = np.array(cutoff) / nyq
        b, a = butter(order, normal_cutoff, btype=btype, analog=False)
        return filtfilt(b, a, data)

    def config_plots(self):
        #self.line_raw, = self.ax.plot([], [], color="gray", alpha=0.5, label="Red (raw)")
        self.line_filt, = self.ax.plot([], [], color="red", label="Red (filtered)")

        self.ax.legend()
        self.ax.set_xlim(0, self.window_size)  

        self.ax.set_ylabel("Intensidad (a.u.)")
        self.ax.legend()
        self.ax.set_title("PPG - Señal cruda vs filtrada (tiempo real)")


    def moving_average(data, window_size=10):
        if len(data) < window_size:
            return np.array([])
        return np.convolve(data, np.ones(window_size)/window_size, mode='valid')


    def update(self, frame):
        if self.ser.in_waiting > 0:
            data = self.ser.readline().decode('utf-8', errors='replace').strip()
            if "Red:" in data:
                try:
                    red = int(data.split("Red:")[1].split(",")[0])
                    self.red_values.append(red)
                except Exception:
                    pass

        # Mantener ventana de muestras
      #  if len(self.red_values) > self.window_size:
       #     self.red_values[:] = self.red_values[-self.window_size:]

        xdata = np.arange(len(self.red_values))
        ydata = np.array(self.red_values)

        # Señal cruda
       # self.line_raw.set_data(xdata, ydata)

        # Señal filtrada: Butterworth + media móvil
        if len(ydata) > 27:
            y_centered = ydata - np.mean(ydata)
            y_filt = self.butterworth_filter(ydata, fs=self.fs, cutoff=[0.5, 15], btype="bandpass", order=4)
            self.line_filt.set_data(xdata, y_filt)

            if len(self.red_values) > 0:
                ymin = min(y_filt)
                ymax = max(y_filt)
                if ymin == ymax:
                    ymin -= 1
                    ymax += 1
                self.ax.set_ylim(-ymin,ymax)
        else:   
            self.line_filt.set_data([], [])


            # Mantener ventana de muestras
        if len(self.red_values) > self.window_size:
            self.red_values[:] = self.red_values[-self.window_size:]

            # Ajustar eje Y
        # if len(self.red_values) > 0:
        #     ymin = min(y_filt)
        #     ymax = max(y_filt)
        #     if ymin == ymax:
        #         ymin -= 1
        #         ymax += 1
        #     self.ax.set_ylim(ymin, ymax)

        return self.line_filt

    def animation(self):
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=1000/self.fs, blit=False,
                                           cache_frame_data=False)   
        plt.show()
        self.ser.close()


if __name__ == "__main__":

    prueba = realtime()
    prueba.animation()

