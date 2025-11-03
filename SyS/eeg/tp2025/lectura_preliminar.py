""" Lectura para obtener frecuencia de muestreo de los archivos """
import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt

# === EEG ===
eeg_data = sio.loadmat('EEG8C_Alfa.mat')
EEG = eeg_data['ALLEEG'][0, 0]  # Estructura MATLAB tipo struct
eeg = EEG['data']               # Señales
chanlocs = EEG['chanlocs']      # Etiquetas de canales
fs = EEG['srate'][0, 0]         # Frecuencia de muestreo

canales, N = eeg.shape
print(f"EEG: {canales} canales, {N} muestras, fs = {fs} Hz")

# === PEA ===
pea_data = sio.loadmat('PEA.mat')
PE = pea_data['ALLEEG'][0, 0]
pe = PE['data']
eventos = PE['event'][0]        # Lista de estructuras con latencia
fs_pe = PE['srate'][0, 0]

# Extraer tiempos de estímulos
latencias = [ev['latency'][0, 0] for ev in eventos]

print(f"PEA: {pe.shape[0]} canales, {pe.shape[1]} muestras, fs = {fs_pe} Hz")
print(f"Cantidad de estímulos: {len(latencias)}")
