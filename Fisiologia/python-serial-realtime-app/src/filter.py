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
