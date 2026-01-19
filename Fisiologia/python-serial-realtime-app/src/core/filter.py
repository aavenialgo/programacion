from scipy.signal import butter, filtfilt, firwin, lfilter
import numpy as np

# def butter_bandpass(lowcut, highcut, fs, order=4):
#     nyq = 0.5 * fs
#     low = lowcut / nyq
#     high = highcut / nyq
#     b, a = butter(order, [low, high], btype="band")
#     return b, a

# def apply_filter(data, lowcut, highcut, fs, order=4):
#     b, a = butter_bandpass(lowcut, highcut, fs, order=order)
#     y = filtfilt(b, a, data)
#     return y

def apply_filter(data, lowcut, highcut, fs, order=4):
    """Aplica un filtro butterworth pasa banda a los datos
    Args:
        data (np.ndarray): señal de entrada
        lowcut (float): frecuencia de corte baja
        highcut (float): frecuencia de corte alta
        fs (int): frecuencia de muestreo
        order (int, optional): orden del filtro. Defaults to 4.

    Returns:
        np.ndarray: señal filtrada
        
    Raises:
        ValueError: si los parámetros no son válidos
    """
    # Validar que hay datos
    if data is None or len(data) == 0:
        raise ValueError("No hay datos para filtrar")
    
    # Validar parámetros del filtro
    if lowcut >= highcut:
        raise ValueError("La frecuencia de corte baja debe ser menor que la alta")
    
    nyq = 0.5 * fs
    if highcut >= nyq:
        raise ValueError(f"La frecuencia de corte alta debe ser menor que fs/2 ({nyq} Hz)")
    
    if lowcut <= 0:
        raise ValueError("La frecuencia de corte baja debe ser positiva")
    
    if order < 1:
        raise ValueError("El orden del filtro debe ser al menos 1")
    
    # Aplicar el filtro
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    y = filtfilt(b, a, data)
    return y

def linebase_removal(data, fs):
    """Elimina la línea base de la señal
    Args:
        data (np.ndarray): señal de entrada
        fs (int): frecuencia de muestreo

    Returns:
        np.ndarray: señal sin componente DC 
    """
    N = len(data)
    if N == 0:
        return data
    F = np.fft.fft(data)
    freqs = np.fft.fftfreq(N, d=1/fs)
    F_noDC = F.copy()
    # Buscar el índice más cercano a 0 Hz (evita comparar floats exactamente)
    idx_dc = np.argmin(np.abs(freqs))
    F_noDC[idx_dc] = 0
    y_noDC = np.fft.ifft(F_noDC).real
    return y_noDC


# def filter(data, lowcut, highcut, fs, order=4):
#     nyq = 0.5 * fs
#     low = lowcut / nyq
#     high = highcut / nyq
#     b, a = butter(order, [low, high], btype="band")
#     y = filtfilt(b, a, data)
#     return y

# def filterPassBand(data, lowcut, highcut, fs, order=4):
#     numtaps = 501
#     b = firwin(numtaps, [lowcut, highcut], pass_zero=False, fs=fs)
#     y = lfilter(b, 1.0, data)
#     # Compensar retraso
#     delay = (numtaps - 1) // 2
#     y_corrected = np.roll(y, -delay)
#     # Opcional: poner los últimos "delay" valores a NaN
#     y_corrected[-delay:] = np.nan
#     return y

# def moving_average(data, window_size=10):
#     if len(data) < window_size:
#         return np.array([])
#     return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

if __name__ == '__main__':
    from src.data.read_data import load_ppg_from_csv
    
    import matplotlib.pyplot as plt

    filepath = 'src/data/para_prueba_senal_suavizada.csv'
    signal, fs = load_ppg_from_csv(filepath)

    if signal is not None and fs is not None:
        filtered_signal = apply_filter(signal, 0.5, 5.0, fs, order=4)
        print("Filtered signal:", filtered_signal)
        time_axis = np.arange(len(signal)) / fs
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(time_axis, signal, label='Original Signal')
        plt.title('Original PPG Signal')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.subplot(2, 1, 2)
        plt.plot(time_axis, filtered_signal, label='Filtered Signal', color='orange')
        plt.title('Filtered PPG Signal (0.5-5 Hz Bandpass)')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.tight_layout()
        plt.show()