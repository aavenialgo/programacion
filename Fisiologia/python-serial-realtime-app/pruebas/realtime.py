import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.signal import butter, filtfilt

#------------------------ Parametros----------------------

#---------------------- Funciones ------------------------
def butterworth_filter(data, fs, cutoff, btype='low', order=4):
    nyq = 0.5 * fs
    normal_cutoff = np.array(cutoff) / nyq
    b, a = butter(order, normal_cutoff, btype=btype, analog=False)
    return filtfilt(b, a, data)

def moving_average(data, window_size=10):
    if len(data) < window_size:
        return np.array([])
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')


def set_value(value):
    return value


# Preparar figura



def update(frame):
    # Leer del puerto serie
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8', errors='replace').strip()
        if "Red:" in data:
            try:
                red = int(data.split("Red:")[1].split(",")[0])
                red_values.append(red)

            except Exception:
                pass

    # Mantener ventana de muestras

    if len(red_values) > window_size:
        red_values[:] = red_values[-window_size:]

    xdata = np.arange(len(red_values))
    ydata = np.array(red_values)
    luz_red = set_value(red_values)
    # Señal cruda
   # line_raw.set_data(xdata, ydata)

    # Señal filtrada solo si hay suficientes datos
    if len(ydata) > 27:
        y_centered = ydata 
        y_butter = butterworth_filter(y_centered, fs=fs, cutoff=[0.5, 15], btype="bandpass", order=4)
        if len (ydata) >= 10:
            y_filt  = moving_average(y_butter, window_size=10)
            x_filt = xdata[:len(y_filt)]
            line_filt.set_data(x_filt, y_filt)
        else:
            line_filt.set_data([], [])
    else:
        line_filt.set_data([], [])
    return line_filt


if __name__ == "__main__":
    fs = 100
    window_sec = 1
    window_size = fs * window_sec
    serial_port = '/dev/ttyUSB0'
    baudrate = 115200
    # Buffer de datos
    red_values = []
    luz_red = red_values

    fig, ax = plt.subplots()
    line_raw, = ax.plot([], [], color="gray", alpha=0.5, label="Red (raw)")
    line_filt, = ax.plot([], [], color="red", label="Red (filtered)")

    ax.legend()
    ax.set_xlim(0, window_size)
    ax.set_ylabel("Intensidad (a.u.)")
    ax.legend()
    ax.set_title("PPG - Señal cruda vs filtrada (tiempo real)")


    # Inicializar puerto serie
    ser = serial.Serial(serial_port, baudrate, timeout=1)


    ani = animation.FuncAnimation(fig, update, interval=1000/fs, blit=False)
    ax.set_ylim(min(luz_red)-200, max(luz_red)+200)

    plt.show()

    ser.close()