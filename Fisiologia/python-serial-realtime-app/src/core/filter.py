from scipy.signal import butter, filtfilt, firwin, lfilter
import numpy as np

def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    return b, a

def apply_filter(data, lowcut, highcut, fs, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def filter(data, lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    y = filtfilt(b, a, data)
    return y

def filterPassBand(data, lowcut, highcut, fs, order=4):
    numtaps = 501
    b = firwin(numtaps, [lowcut, highcut], pass_zero=False, fs=fs)
    y = lfilter(b, 1.0, data)
    # Compensar retraso
    delay = (numtaps - 1) // 2
    y_corrected = np.roll(y, -delay)
    # Opcional: poner los últimos "delay" valores a NaN
    y_corrected[-delay:] = np.nan
    return y

def moving_average(data, window_size=10):
    if len(data) < window_size:
        return np.array([])
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

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