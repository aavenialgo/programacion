"""Acondicionamiento de la señal ECG mediante filtrado en frecuencia y detección de picos QRS.
@author: Andres Venialgo
@author: Nazarena Romero
"""
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np
from scipy.fft import fft, ifft
import wfdb
from wfdb import processing


FILE= "ecg_con_ruido.txt"
def load_ecg(path=FILE):
    """Carga el archivo y devuelve la señal ECG.
    """
    data = np.loadtxt(path)
    if data.ndim > 1:
        data = data[:, 0]
    return data


def grafica_ecg(ecg_signal, fs):
    """Grafica la señal ECG.
    """
    t = np.arange(len(ecg_signal)) / fs
    plt.figure(figsize=(10, 4))
    plt.plot(t, ecg_signal, label='ECG Signal')
    plt.title('ECG Signal')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid()
    plt.legend()
    plt.show()

def graf_frecuency(ecg_signal, fs):
    """Grafica la FFT de la señal ECG.
    """
    N = len(ecg_signal)
    freq = np.fft.fftfreq(N, d=1/fs)
    ecg_fft = np.fft.fft(ecg_signal)
    plt.figure(figsize=(10, 4))
    plt.plot(freq[:N//2], np.abs(ecg_fft)[:N//2], label='FFt de la señal ECG')
    plt.title('FFT de la señal ECG')
    plt.xlabel('Frecuencia (Hz)')
    plt.ylabel('Magnitud')
    plt.grid()
    plt.legend()
    plt.show()

def detectarQRS(ecg_signal, fs):
    """Detecta los picos QRS en la señal ECG.
    """
    time_sec = np.arange(len(ecg_signal)) / fs
    plt.plot(time_sec, ecg_signal, label='ECG con Ruido', linewidth=1)
    #graficar picos detectados
    r_peaks_indices = processing.xqrs_detect(sig=ecg_signal, fs=fs)
    r_peaks_time = r_peaks_indices / fs
    r_peaks_amplitude = ecg_signal[r_peaks_indices]
    
    plt.plot(r_peaks_time, r_peaks_amplitude, 'o', color='red', markersize=6, label='Picos R detectados')

    plt.title(f'Señal ECG y Picos R detectados (FS: {fs} Hz)')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('Amplitud (Unidades AD)')
    plt.legend()
    plt.grid(True)
    plt.show()

    return  None
if __name__ == "__main__":
    ecg_signal = load_ecg()
    fs = 360
    # Grafico señal original con ruido
    grafica_ecg(ecg_signal, fs)
    fft_ecg = fft(ecg_signal)
    graf_frecuency(ecg_signal, fs)

    deltaf = fs / len(ecg_signal)
    fft_D2 = fft(ecg_signal)
    #defino bandas de frecuencia 
    f10 = round((10 / deltaf) - 1)
    f25 = round((25 / deltaf) - 1)
    f180 = round((180 / deltaf) - 1)
    f335 = 2 * f180 - f25
    f345 = 2 * f180 - f10
    #Filtrado en frecuencia
    fft_D2_filtrada = np.zeros_like(fft_D2, dtype=complex)
    fft_D2_filtrada[f10:f25+1] = fft_D2[f10:f25+1]
    fft_D2_filtrada[f335:f345+1] = fft_D2[f335:f345+1]
    # volver al dominio del tiempo
    ecg_signal = np.real(ifft(fft_D2_filtrada))
    ecg_filtrada_ploteo = fft_D2_filtrada.copy()
    # Grafico señal filtrada
    grafica_ecg(ecg_signal, fs)
    fft_ecg = fft(ecg_signal)
    graf_frecuency(ecg_signal, fs)
    # Detección de picos QRS
    detectarQRS(ecg_signal, fs)



    

