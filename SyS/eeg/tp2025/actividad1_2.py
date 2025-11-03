""" Análisis tiempo-frecuencia de canales F4 y O2 para identificar ritmo alfa
    @author: Andres Venialgo
    @author: Nazarena Romero
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy.signal import spectrogram, welch
from scipy import signal

# Carga de datos
data = sio.loadmat('EEG8C_Alfa.mat')
EEG = data['ALLEEG'][0, 0]

eeg = EEG['data']
fs = 250

# Seleccionar canales F4 y O2 (ajustar índices según tu archivo)
# Verificar primero qué canales tienes disponibles
print("Información de canales:")
print(f"Forma de los datos EEG: {eeg.shape}")
print(f"Número de canales: {eeg.shape[0]}")

canal_F4 = eeg[1,:]  # Ajustar índice según corresponda
canal_O2 = eeg[7,:]  # Ajustar índice según corresponda


duracion = 20  # segundos
N = fs * duracion

# Tomar solo los primeros 20 segundos
F4_signal = canal_F4[:N]
O2_signal = canal_O2[:N]

# Parámetros para análisis tiempo-frecuencia
ventana_tf = 'hann'  # Ventana para espectrograma
nperseg = fs * 2     # 2 segundos por segmento
noverlap = nperseg // 2  # 50% de overlap

# Análisis tiempo-frecuencia usando espectrograma
print("Calculando espectrogramas...")

# Canal F4
f_F4, t_F4, Sxx_F4 = spectrogram(F4_signal, fs=fs, window=ventana_tf, 
                                  nperseg=nperseg, noverlap=noverlap, 
                                  scaling='density')

# Canal O2
f_O2, t_O2, Sxx_O2 = spectrogram(O2_signal, fs=fs, window=ventana_tf, 
                                  nperseg=nperseg, noverlap=noverlap, 
                                  scaling='density')

# Análisis específico del ritmo alfa (8-12 Hz)
idx_alfa = np.where((f_F4 >= 8) & (f_F4 <= 12))[0]

# Potencia promedio en banda alfa para cada canal
potencia_alfa_F4 = np.mean(Sxx_F4[idx_alfa, :], axis=0)
potencia_alfa_O2 = np.mean(Sxx_O2[idx_alfa, :], axis=0)

# Estadísticas del ritmo alfa
print("\nAnálisis del ritmo alfa (8-12 Hz):")
print(f"Canal F4 - Potencia alfa promedio: {np.mean(potencia_alfa_F4):.2e}")
print(f"Canal F4 - Desviación estándar: {np.std(potencia_alfa_F4):.2e}")
print(f"Canal O2 - Potencia alfa promedio: {np.mean(potencia_alfa_O2):.2e}")
print(f"Canal O2 - Desviación estándar: {np.std(potencia_alfa_O2):.2e}")

ratio_alfa = np.mean(potencia_alfa_O2) / np.mean(potencia_alfa_F4)
print(f"Ratio O2/F4 en banda alfa: {ratio_alfa:.2f}")

# Gráficos
plt.figure(figsize=(15, 12))

# Señales temporales
plt.subplot(3, 2, 1)
tiempo = np.arange(N) / fs
plt.plot(tiempo, F4_signal)
plt.title('Canal F4 - Señal temporal')
plt.xlabel('Tiempo [s]')
plt.ylabel('Amplitud [μV]')
plt.grid(True)

plt.subplot(3, 2, 2)
plt.plot(tiempo, O2_signal)
plt.title('Canal O2 - Señal temporal')
plt.xlabel('Tiempo [s]')
plt.ylabel('Amplitud [μV]')
plt.grid(True)

# Espectrogramas
plt.subplot(3, 2, 3)
plt.pcolormesh(t_F4, f_F4, 10*np.log10(Sxx_F4), shading='gouraud', cmap='jet')
plt.colorbar(label='PSD [dB]')
plt.ylim(0, 30)
plt.title('Espectrograma Canal F4')
plt.xlabel('Tiempo [s]')
plt.ylabel('Frecuencia [Hz]')

plt.subplot(3, 2, 4)
plt.pcolormesh(t_O2, f_O2, 10*np.log10(Sxx_O2), shading='gouraud', cmap='jet')
plt.colorbar(label='PSD [dB]')
plt.ylim(0, 30)
plt.title('Espectrograma Canal O2')
plt.xlabel('Tiempo [s]')
plt.ylabel('Frecuencia [Hz]')

# Evolución temporal del ritmo alfa
plt.subplot(3, 2, 5)
plt.plot(t_F4, potencia_alfa_F4, 'b-', linewidth=2, label='F4')
plt.plot(t_O2, potencia_alfa_O2, 'r-', linewidth=2, label='O2')
plt.title('Evolución temporal del ritmo alfa (8-12 Hz)')
plt.xlabel('Tiempo [s]')
plt.ylabel('Potencia promedio [V²/Hz]')
plt.legend()
plt.grid(True)

# PSD promedio de toda la señal
plt.subplot(3, 2, 6)
f_psd_F4, psd_F4 = welch(F4_signal, fs=fs, nperseg=fs*2)
f_psd_O2, psd_O2 = welch(O2_signal, fs=fs, nperseg=fs*2)

plt.semilogy(f_psd_F4, psd_F4, 'b-', linewidth=2, label='F4')
plt.semilogy(f_psd_O2, psd_O2, 'r-', linewidth=2, label='O2')
plt.axvspan(8, 12, alpha=0.3, color='yellow', label='Banda alfa')
plt.xlim(0, 30)
plt.title('PSD promedio - Comparación F4 vs O2')
plt.xlabel('Frecuencia [Hz]')
plt.ylabel('PSD [V²/Hz]')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# Análisis cuantitativo adicional
print("\n" + "="*50)
print("ANÁLISIS CUANTITATIVO DEL RITMO ALFA")
print("="*50)

# Encontrar pico dominante en banda alfa
idx_pico_F4 = np.argmax(psd_F4[(f_psd_F4 >= 8) & (f_psd_F4 <= 12)])
idx_pico_O2 = np.argmax(psd_O2[(f_psd_O2 >= 8) & (f_psd_O2 <= 12)])

freq_alfa_F4 = f_psd_F4[(f_psd_F4 >= 8) & (f_psd_F4 <= 12)][idx_pico_F4]
freq_alfa_O2 = f_psd_O2[(f_psd_O2 >= 8) & (f_psd_O2 <= 12)][idx_pico_O2]

print(f"Frecuencia de pico alfa F4: {freq_alfa_F4:.2f} Hz")
print(f"Frecuencia de pico alfa O2: {freq_alfa_O2:.2f} Hz")

# Potencia total en diferentes bandas
def calcular_potencia_banda(f, psd, f_min, f_max):
    idx = (f >= f_min) & (f <= f_max)
    return np.trapz(psd[idx], f[idx])

# Bandas de frecuencia estándar
bandas = {
    'Delta (0.5-4 Hz)': (0.5, 4),
    'Theta (4-8 Hz)': (4, 8),
    'Alfa (8-12 Hz)': (8, 12),
    'Beta (12-30 Hz)': (12, 30)
}

print(f"\nPotencia por bandas:")
print(f"{'Banda':<20} {'F4':<15} {'O2':<15} {'Ratio O2/F4':<15}")
print("-" * 65)

for banda, (f_min, f_max) in bandas.items():
    pot_F4 = calcular_potencia_banda(f_psd_F4, psd_F4, f_min, f_max)
    pot_O2 = calcular_potencia_banda(f_psd_O2, psd_O2, f_min, f_max)
    ratio = pot_O2 / pot_F4
    print(f"{banda:<20} {pot_F4:<15.2e} {pot_O2:<15.2e} {ratio:<15.2f}")

print("\n" + "="*50)
print("CONCLUSIÓN:")
if ratio_alfa > 1.5:
    print("El ritmo alfa se manifiesta MÁS CLARAMENTE en el canal O2")
elif ratio_alfa < 0.67:
    print("El ritmo alfa se manifiesta MÁS CLARAMENTE en el canal F4")
else:
    print("El ritmo alfa se manifiesta de forma SIMILAR en ambos canales")
print(f"Ratio de potencia alfa O2/F4: {ratio_alfa:.2f}")
print("="*50)