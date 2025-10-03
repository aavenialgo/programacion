import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Parámetros
fs = 100               # frecuencia de muestreo en Hz
window_sec = 3         # segundos de ventana
window_size = fs * window_sec  # muestras en la ventana

# Leer log y parsear
red_values = []
ir_values = []

with open("ppg.log", "r") as f:
    for line in f:
        if "Red:" in line and "IR:" in line:
            parts = line.strip().replace(">", "").split(",")
            red = int(parts[0].split(":")[1])
            ir = int(parts[1].split(":")[1])
            red_values.append(red)
            ir_values.append(ir)

# Convertir a numpy arrays
red_values = np.array(red_values)
ir_values = np.array(ir_values)

# Preparar la figura
fig, ax = plt.subplots()
line_red, = ax.plot([], [], label="Red", color="red")
line_ir, = ax.plot([], [], label="IR", color="blue")

ax.set_xlim(0, window_size)
ax.set_ylim(min(min(red_values), min(ir_values)) - 100,
            max(max(red_values), max(ir_values)) + 100)
ax.legend()
ax.set_xlabel("Muestras")
ax.set_ylabel("Intensidad (a.u.)")
ax.set_title("PPG señal simulada en tiempo real")

# Función de actualización
def update(frame):
    start = max(0, frame - window_size)
    xdata = np.arange(start, frame)
    line_red.set_data(xdata - start, red_values[start:frame])
    line_ir.set_data(xdata - start, ir_values[start:frame])
    return line_red, line_ir

ani = animation.FuncAnimation(fig, update, frames=len(red_values),
                              interval=1000/fs, blit=True, repeat=True)

plt.show()
