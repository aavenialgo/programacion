import numpy as np
import matplotlib.pyplot as plt
import serial
from scipy.signal import butter, filtfilt
from filter import filter

# ==== Parámetros ====
fs = 100  # Frecuencia de muestreo en Hz
lowcut = 0.5  # Hz
highcut = 21  # Hz

# Configuración del puerto serie
ser = serial.Serial('/dev/ttyUSB0', baudrate=115200, timeout=1)

# Inicialización de listas para almacenar datos
red = []
ir = []

plt.ion()  # Modo interactivo para graficar en tiempo real
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

while True:
    line = ser.readline().decode('utf-8').strip()
    if line.startswith(">"):
        line = line[1:]  # Quita el >
        parts = line.split(",")
        vals = {}
        for p in parts:
            k, v = p.split(":")
            vals[k] = float(v)
        red.append(vals.get("Red", 0))
        ir.append(vals.get("IR", 0))

        if len(red) > fs:  # Limitar la longitud de los datos
            red = red[-fs:]
            ir = ir[-fs:]

        red_filt = filter(np.array(red), lowcut, highcut, fs)
        ir_filt = filter(np.array(ir), lowcut, highcut, fs)

        t = np.arange(len(red)) / fs

        ax1.clear()
        ax1.plot(t, red, label="Red (crudo)", color="red", alpha=0.4)
        ax1.plot(t, red_filt, label="Red (filtrado)", color="darkred")
        ax1.legend()
        ax1.set_ylabel("Red")
        ax1.set_title("Señal Red")

        ax2.clear()
        ax2.plot(t, ir, label="IR (crudo)", color="gray", alpha=0.4)
        ax2.plot(t, ir_filt, label="IR (filtrado)", color="black")
        ax2.legend()
        ax2.set_ylabel("IR")
        ax2.set_xlabel("Tiempo (s)")
        ax2.set_title("Señal IR")

        plt.tight_layout()
        plt.pause(0.01)  # Pausa para actualizar la gráfica

ser.close()