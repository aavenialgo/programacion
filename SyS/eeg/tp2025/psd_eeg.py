""" Analisis de señal EEG con metodo parametrico (Burg) y no parametrico (Welch) 
    @author: Andres Venialgo
    @author: Nazarena Romero
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy.signal import welch
from spectrum import arburg

# Carga de datos
data = sio.loadmat('EEG8C_Alfa.mat')
EEG = data['ALLEEG'][0, 0]

eeg = EEG['data']
fs = 250

canal_F3 = eeg[0,:] #f3 es el primer canal

duracion_total = 20 # segundos
duracion_ventana = 1 # segundo por ventana
N_ventana = fs * duracion_ventana
N_total = fs * duracion_total

# Parámetros
order_burg = 15
n_ventanas = duracion_total // duracion_ventana

# Arrays para almacenar resultados
f_welch = None
f_burg = np.linspace(0, fs/2, 512)
psd_welch_total = []
psd_burg_total = []

# Analizar ventanas consecutivas de 1 segundo
for i in range(n_ventanas):
    inicio = i * N_ventana
    fin = (i + 1) * N_ventana
    ventana = canal_F3[inicio:fin]
    
    # Método de Welch para la ventana
    f_w, psd_w = welch(ventana, fs=fs, nperseg=N_ventana//4, noverlap=N_ventana//8)
    if f_welch is None:
        f_welch = f_w
    psd_welch_total.append(psd_w)
    
    # Método de Burg para la ventana
    AR, P, k = arburg(ventana, order=order_burg)
    
    # Calcular PSD del modelo AR
    H = np.zeros(len(f_burg), dtype=complex)
    for j, freq in enumerate(f_burg):
        omega = 2 * np.pi * freq / fs
        z = np.exp(1j * omega)
        denominator = 1 + np.sum([AR[k] * (z**(-k-1)) for k in range(len(AR))])
        H[j] = 1 / denominator
    
    psd_burg = P * np.abs(H)**2
    psd_burg_total.append(psd_burg)

# Convertir a arrays numpy
psd_welch_total = np.array(psd_welch_total)
psd_burg_total = np.array(psd_burg_total)

# Calcular PSD promedio de todas las ventanas
psd_welch_promedio = np.mean(psd_welch_total, axis=0)
psd_burg_promedio = np.mean(psd_burg_total, axis=0)

# Gráfico comparativo
plt.figure(figsize=(12, 8))

# Subplot 1: Comparación de métodos promediados
plt.subplot(2, 1, 1)
plt.semilogy(f_welch, psd_welch_promedio, label='Welch (promedio)', linewidth=2)
plt.semilogy(f_burg, psd_burg_promedio, label=f'Burg (promedio, orden {order_burg})', linewidth=2)
plt.xlim(0, 40)
plt.xlabel('Frecuencia [Hz]')
plt.ylabel('PSD [V²/Hz]')
plt.title('Comparación PSD promedio: Welch vs Burg (20 ventanas de 1 seg)')
plt.legend()
plt.grid(True)

# Subplot 2: Evolucion temporal (primeras 5 ventanas)
plt.subplot(2, 1, 2)
for i in range(min(5, n_ventanas)):
    plt.semilogy(f_welch, psd_welch_total[i], alpha=0.6, label=f'Ventana {i+1}' if i < 3 else '')
plt.xlim(0, 40)
plt.xlabel('Frecuencia [Hz]')
plt.ylabel('PSD [V²/Hz]')
plt.title('Evolución temporal PSD Welch (primeras 5 ventanas)')
plt.legend()
plt.grid(True)

# plt.tight_layout()
# plt.show()

# # Análisis estadístico
# print(f"Número de ventanas analizadas: {n_ventanas}")
# print(f"Duración de cada ventana: {duracion_ventana} segundos")
# print(f"Frecuencia de muestreo: {fs} Hz")
# print(f"Orden del modelo AR (Burg): {order_burg}")

plt.tight_layout()
plt.show()

# Verificaciones y análisis de resultados
print("="*50)
print("VERIFICACIONES DEL ANÁLISIS")
print("="*50)

# 1. Verificar dimensiones
print(f"Número de ventanas analizadas: {n_ventanas}")
print(f"Duración de cada ventana: {duracion_ventana} segundos")
print(f"Frecuencia de muestreo: {fs} Hz")
print(f"Orden del modelo AR (Burg): {order_burg}")
print(f"Puntos por ventana: {N_ventana}")

# 2. Verificar vectores de frecuencia
print(f"\nRango de frecuencias Welch: {f_welch[0]:.2f} - {f_welch[-1]:.2f} Hz")
print(f"Rango de frecuencias Burg: {f_burg[0]:.2f} - {f_burg[-1]:.2f} Hz")
print(f"Resolución frecuencial Welch: {f_welch[1]-f_welch[0]:.2f} Hz")
print(f"Resolución frecuencial Burg: {f_burg[1]-f_burg[0]:.2f} Hz")

# 3. Verificar consistencia de dimensiones
print(f"\nDimensiones PSD Welch: {psd_welch_total.shape}")
print(f"Dimensiones PSD Burg: {psd_burg_total.shape}")

# 4. Buscar pico de alfa (8-12 Hz para EEG)
idx_alfa_welch = np.where((f_welch >= 8) & (f_welch <= 12))[0]
idx_alfa_burg = np.where((f_burg >= 8) & (f_burg <= 12))[0]

if len(idx_alfa_welch) > 0 and len(idx_alfa_burg) > 0:
    pico_alfa_welch = f_welch[idx_alfa_welch[np.argmax(psd_welch_promedio[idx_alfa_welch])]]
    pico_alfa_burg = f_burg[idx_alfa_burg[np.argmax(psd_burg_promedio[idx_alfa_burg])]]
    
    print(f"\nPico en banda alfa:")
    print(f"Welch: {pico_alfa_welch:.2f} Hz")
    print(f"Burg: {pico_alfa_burg:.2f} Hz")
    print(f"Diferencia: {abs(pico_alfa_welch - pico_alfa_burg):.2f} Hz")

# 5. Verificar potencia total
potencia_welch = np.trapz(psd_welch_promedio, f_welch)
potencia_burg = np.trapz(psd_burg_promedio, f_burg)
print(f"\nPotencia total:")
print(f"Welch: {potencia_welch:.2e}")
print(f"Burg: {potencia_burg:.2e}")
print(f"Ratio Burg/Welch: {potencia_burg/potencia_welch:.2f}")

# 6. Análisis de variabilidad entre ventanas
variabilidad_welch = np.std(psd_welch_total, axis=0)
variabilidad_burg = np.std(psd_burg_total, axis=0)

print(f"\nVariabilidad promedio entre ventanas:")
print(f"Welch: {np.mean(variabilidad_welch):.2e}")
print(f"Burg: {np.mean(variabilidad_burg):.2e}")

# 7. Gráfico adicional de verificación
plt.figure(figsize=(12, 10))

# Señal original
plt.subplot(3, 1, 1)
tiempo = np.arange(N_total) / fs
plt.plot(tiempo[:5000], canal_F3[:5000])  # Primeros 20 segundos
plt.xlabel('Tiempo [s]')
plt.ylabel('Amplitud [μV]')
plt.title('Señal EEG original (primeros 20 seg)')
plt.grid(True)

# Comparación en escala lineal
plt.subplot(3, 1, 2)
plt.plot(f_welch, psd_welch_promedio, label='Welch (promedio)', linewidth=2)
plt.plot(f_burg, psd_burg_promedio, label=f'Burg (promedio, orden {order_burg})', linewidth=2)
plt.xlim(0, 40)
plt.xlabel('Frecuencia [Hz]')
plt.ylabel('PSD [V²/Hz]')
plt.title('Comparación PSD - Escala lineal')
plt.legend()
plt.grid(True)

# Variabilidad entre ventanas
plt.subplot(3, 1, 3)
plt.plot(f_welch, variabilidad_welch/psd_welch_promedio, label='CV Welch', linewidth=2)
plt.plot(f_burg, variabilidad_burg/psd_burg_promedio, label='CV Burg', linewidth=2)
plt.xlim(0, 40)
plt.xlabel('Frecuencia [Hz]')
plt.ylabel('Coeficiente de Variación')
plt.title('Variabilidad relativa entre ventanas')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

print("\n" + "="*50)
print("CRITERIOS DE VALIDACIÓN:")
print("- Los picos en alfa (8-12 Hz) deben ser consistentes")
print("- La potencia total debe ser del mismo orden de magnitud")
print("- La variabilidad debe ser razonable (CV < 1)")
print("- Los métodos deben mostrar tendencias similares")
print("="*50)