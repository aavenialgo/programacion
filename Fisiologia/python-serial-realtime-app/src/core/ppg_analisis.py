""" 
Modulo de analisis de señales PPG.
Lo que hace es analizar señales PPG para extraer características temporales y de amplitud.
Usa la librería HeartPy para el análisis temporal y SciPy para el análisis de amplitud """
import numpy as np
import heartpy as hp
from scipy.signal import butter, filtfilt
import pandas as pd

# --- Filtros (Helpers) ---

def _butter_lowpass_filter(data, cutoff, fs, order=4):
    """
    Aplica un filtro Butterworth low-pass de orden 'order'.
    Usa filtfilt para evitar desfase.
    """
    nyq = 0.5 * fs  # Frecuencia de Nyquist
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

# --- Funciones Principales del Módulo ---


def get_dc_component(ppg_signal, fs, cutoff=0.5):
    """
    Calcula el componente DC (Basal) de la señal PPG.
    Filtra la señal por debajo del 'cutoff' (0.5 Hz por defecto) y calcula la media.
    """
    dc_signal = _butter_lowpass_filter(ppg_signal, cutoff, fs)
    return np.mean(dc_signal)

def get_ac_component(ppg_signal, fs, dc_cutoff=0.5, ac_noise_cutoff=4.0):
    """
    Calcula el componente AC (Pulsátil) de la señal PPG.
    Mide la amplitud pico a pico (max - min) de la señal pulsátil.
    """
    dc_signal = _butter_lowpass_filter(ppg_signal, dc_cutoff, fs)
    ac_signal = ppg_signal - dc_signal
    ac_signal_filtered = _butter_lowpass_filter(ac_signal, ac_noise_cutoff, fs)
    return np.max(ac_signal_filtered) - np.min(ac_signal_filtered)
# --- Funciones Principales del Módulo ---

def get_temporal_features(ppg_signal, fs):
    """
    Calcula características temporales usando HeartPy.
    
    Devuelve:
    - FC (Frecuencia Cardíaca) en BPM.
    - PPI (Intervalo Pulso-Pulso) promedio en ms.
    - Índices de los picos sistólicos.
    - working_data: Diccionario de HeartPy con datos procesados.
    - measures: Diccionario de HeartPy con las métricas.
    """
    try:
        # se usa heartpy.process para obtener el análisis
        working_data, measures = hp.process(ppg_signal, sample_rate=fs)
        
        fc_bpm = measures.get('bpm', np.nan)
        ppi_ms = measures.get('ibi', np.nan) # HeartPy lo llama 'ibi' (Inter-Beat Interval)
        
        # se obtiene la lista de picos sistólicos (índices)
        systolic_peaks_idx = working_data.get('peaklist', np.array([]))
        
        return fc_bpm, ppi_ms, systolic_peaks_idx, working_data, measures
        
    except Exception as e:
        # HeartPy puede fallar si la señal es demasiado ruidosa
        print(f"Error en el procesamiento de HeartPy: {e}")
        return np.nan, np.nan, np.array([]), None, None

def get_dc_component(ppg_signal, fs, cutoff=0.5):
    """
    Calcula el componente DC (Basal) de la señal PPG.
    Filtra la señal por debajo del 'cutoff' (0.5 Hz por defecto) y calcula la media.
    """
    dc_signal = _butter_lowpass_filter(ppg_signal, cutoff, fs)
    return np.mean(dc_signal)

def get_ac_component(ppg_signal, fs, dc_cutoff=0.5, ac_noise_cutoff=4.0):
    """
    Calcula el componente AC (Pulsátil) de la señal PPG.
    Mide la amplitud pico a pico (max - min) de la señal pulsátil.
    """
    dc_signal = _butter_lowpass_filter(ppg_signal, dc_cutoff, fs)
    ac_signal = ppg_signal - dc_signal
    ac_signal_filtered = _butter_lowpass_filter(ac_signal, ac_noise_cutoff, fs)
    return np.max(ac_signal_filtered) - np.min(ac_signal_filtered)



if '__main__' == __name__:
    fs = 125.0
    
    # Cargar datos usando pandas en lugar de hp.get_data()
    df = pd.read_csv('./archivos_csv/analisis_ppg_prueba_1_senal_suavizada.csv')  # sep='\t' para archivos separados por tabulador
    
    signal = df['ppg_suavizada'].values
    tiempo = df['tiempo_s'].values
    
    # Se limita a n segundos
    signal = signal[:int(9 * fs)]
    
    print(f"Datos cargados: {len(signal)} puntos")
    print(f"Primeros 5 valores: {signal[:5]}")
    print(f"Rango de valores: {signal.min():.2f} a {signal.max():.2f}")
    
    # 2. Analisis de la señal usando nuestro módulo
    print(f"\nAnalizando señal de {len(signal)/fs} segundos...\n")

    # --- Temporal (HeartPy) ---
    fc, ppi, peaks, working_data, measures = get_temporal_features(signal, fs)
    print("--- Características Temporales (HeartPy) ---")
    print(f"Frecuencia Cardíaca (FC): {fc:.2f} BPM")
    print(f"Intervalo Pulso-Pulso (PPI): {ppi:.2f} ms")
    print(f"Picos Sistólicos detectados: {len(peaks)} picos\n")

    # --- Amplitud (Scipy) ---
    dc_val = get_dc_component(signal, fs)
    ac_val = get_ac_component(signal, fs)
    print("--- Características de Amplitud (Scipy) ---")
    print(f"Componente DC (Media basal): {dc_val:.4f}")
    print(f"Componente AC (Amplitud P-P): {ac_val:.4f}\n")