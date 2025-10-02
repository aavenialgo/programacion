import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.signal import butter, filtfilt

# Parámetros
fs = 100
window_sec = 3
window_size = fs * window_sec

# Función de filtro
def bandpass_filter(data, lowcut=0.5, highcut=5, fs=100, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    if len(data) > max(len(a), len(b)) * 3:  # condición para evitar error de filtfilt
        return filtfilt(b, a, data)
    else:
        return data  # si no hay suficientes muestras, devolvemos sin filtrar

# Leer log
red_values = []
with open("ppg.log", "r") as f:
    for line in f:
        if "Red:" in line:
            parts = line.strip().replace(">", "").split(",")
            red = int(parts[0].split(":")[1])
            red_values.append(red)

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

    # señal filtrada
    y_filt = bandpass_filter(ydata, lowcut=0.5, highcut=5, fs=fs)
    line_filt.set_data(xdata, y_filt)

    return line_raw, line_filt

ani_crudo = animation.FuncAnimation(fig, update, frames=len(red_values),
                              interval=1000/fs, blit=True, repeat=True)

plt.show()
