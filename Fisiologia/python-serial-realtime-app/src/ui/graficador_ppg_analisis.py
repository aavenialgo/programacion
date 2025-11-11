import pandas as pd
import numpy as np
import ppg_analisis as ppg 
import heartpy as hp

import matplotlib.pyplot as plt

def load_ppg_from_csv(filepath):
    """
    Carga una señal PPG desde el formato CSV 
    """
    try:
        df = pd.read_csv(
            filepath, 
            usecols=["tiempo_s", "ppg_suavizada"]
            #tiempo_s	ppg_suavizada

        )
        signal = df["ppg_suavizada"].to_numpy()
        avg_sample_period = np.mean(np.diff(df["tiempo_s"]))
        fs = 1.0 / avg_sample_period
        
        print(f"Archivo CSV cargado exitosamente. fs calculado: {fs:.2f} Hz")
        return signal, fs
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en '{filepath}'")
        return None, None
    except Exception as e:
        print(f"Error cargando CSV: {e}")
        return None, None

# --- SCRIPT PRINCIPAL ---

# 1. Carga la señal desde tu CSV
ARCHIVO_CSV = './archivos_csv/para_prueba_senal_suavizada.csv'
signal, fs = load_ppg_from_csv(ARCHIVO_CSV)

if signal is not None and fs is not None:
    
    duracion_segundos = len(signal) / fs
    print(f"Analizando señal de {duracion_segundos:.2f} segundos...\n")

    # --- Análisis Temporal ---
    fc, ppi, peaks, heartpy_wd, heartpy_m = ppg.get_temporal_features(signal, fs)
    
    print("--- Características Temporales (HeartPy) ---")
    print(f"Frecuencia Cardíaca (FC): {fc:.2f} BPM")
    print(f"Intervalo Pulso-Pulso (PPI): {ppi:.2f} ms")
    print(f"Picos Sistólicos detectados: {len(peaks)} picos\n")

    # --- Análisis de Amplitud ---
    dc_val = ppg.get_dc_component(signal, fs)
    ac_val = ppg.get_ac_component(signal, fs)
    
    print("--- Características de Amplitud (Scipy) ---")
    print(f"Componente DC (Media basal): {dc_val:.4f}")
    print(f"Componente AC (Amplitud P-P): {ac_val:.4f}\n")


    # --- VISUALIZACIÓN ---
    print("Generando gráficos...")

    # Gráfico 1: Señal PPG con Picos Sistólicos y Componente DC
    # ---------------------------------------------------------
    
    # Creamos un eje de tiempo en segundos para el gráfico
    time_axis = np.arange(len(signal)) / fs
    
    plt.figure(figsize=(15, 5))
    
    # 1. Graficamos la señal PPG completa
    plt.plot(time_axis, signal, label="Señal PPG (PPG Suavizada)", color='cornflowerblue', zorder=1)
    
    if len(peaks) > 0:
        # 2. Marcamos los Picos Sistólicos detectados
        plt.scatter(
            time_axis[peaks],  # Coordenadas X (en segundos)
            signal[peaks],     # Coordenadas Y (valor de la señal)
            color='red', 
            label="Picos Sistólicos (FC, PPI)", 
            marker='x',
            zorder=2
        )
    
    # 3. Graficamos el Componente DC como una línea horizontal
    plt.axhline(
        y=dc_val, 
        color='darkorange', 
        linestyle='--', 
        label=f"Componente DC (Media = {dc_val:.2f})"
    )
    
    plt.title("Análisis de Señal PPG: Picos Sistólicos y Componente DC")
    plt.xlabel("Tiempo (segundos)")
    plt.ylabel("Amplitud PPG")
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.show()


    # Gráfico 2: Diagnóstico completo de HeartPy
    # ---------------------------------------------------------
    # Esto genera 3 gráficos: señal+picos, variabilidad (IBI) y espectro (PSD)
    if heartpy_wd is not None and heartpy_m is not None:
        print("Mostrando gráfico de diagnóstico de HeartPy...")
        
        # Usamos el plotter integrado de HeartPy
        hp.plotter(heartpy_wd, heartpy_m, title="Diagnóstico Completo de HeartPy")
        
        # HeartPy a veces no llama a show() automáticamente
        plt.show()

else:
    print("No se pudo cargar la señal. Finalizando el script.")