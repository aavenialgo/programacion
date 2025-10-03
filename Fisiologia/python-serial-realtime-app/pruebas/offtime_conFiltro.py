import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.signal import butter, filtfilt
import sys

# Parámetros
fs = 100
window_sec = 1
window_size = fs * window_sec

# Función de filtro
def butterworth_filter(data, fs, cutoff, btype='low', order=4):
    """
    data   : señal a filtrar (array)
    fs     : frecuencia de muestreo (Hz)
    cutoff : frecuencia de corte (Hz)
    btype  : tipo de filtro ('low', 'high', 'bandpass', 'bandstop')
    order  : orden del filtro
    """
    nyq = 0.5 * fs                # frecuencia de Nyquist
    normal_cutoff = np.array(cutoff) / nyq  # normalización
    b, a = butter(order, normal_cutoff, btype=btype, analog=False)
    filtered = filtfilt(b, a, data)
    return filtered

# Leer log
red_values = []
try:
    with open("ppg.log", "r") as f:
        for line in f:
            if "Red:" in line:
                parts = line.strip().replace(">", "").split(",")
                red = int(parts[0].split(":")[1])
                red_values.append(red)
except FileNotFoundError:
    print("Error: No se encontró el archivo 'ppg2.log'.")
    sys.exit(1)

red_values = np.array(red_values)

# Preparar figura
fig, ax = plt.subplots()

line_raw, = ax.plot([], [], color="gray", alpha=0.5, label="Red (raw)")
line_filt, = ax.plot([], [], color="red", label="Red (filtered)")

ax.set_xlim(0, window_size)
ax.set_ylim(min(red_values)-200, max(red_values)+200)
ax.set_xlabel("Muestras")
ax.set_ylabel("Intensidad (a.u.)")
ax.legend()
ax.set_title("PPG - Señal cruda vs filtrada (tiempo real)")

# Función de actualización
def update(frame):
    start = max(0, frame - window_size)
    xdata = np.arange(start, frame) - start
    ydata = red_values[start:frame]

    # señal cruda
    line_raw.set_data(xdata, ydata)

    # señal filtrada solo si hay suficientes datos
    if len(ydata) > 27:
        y_filt = butterworth_filter(ydata,fs=fs, cutoff=[0.5,15], btype= "bandpass",order=4) 
        line_filt.set_data(xdata, y_filt)
    else:
        line_filt.set_data([], [])

    return line_filt

ani = animation.FuncAnimation(fig, update, frames=len(red_values),
                              interval=1000/fs, blit=False, repeat=True)

plt.show()
