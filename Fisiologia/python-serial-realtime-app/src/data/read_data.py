"""
Funciones para cargar datos desde archivos CSV
"""
import pandas as pd
import numpy as np

def load_ppg_from_csv(filepath):
    """
    Carga una señal PPG desde el formato CSV 
    """
    try:
        df = pd.read_csv(
            filepath, 
            usecols=["tiempo_s", "valor_filt"]
            #tiempo_s	valor_filt

        )
        signal = df["valor_filt"].to_numpy()
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


if __name__ == "__main__":
    # Ejemplo de uso
    signal, fs = load_ppg_from_csv("datos_filtrados_naza4_filtrado.csv")
    if signal is not None:
        print(f"Señal cargada con {len(signal)} muestras y frecuencia de muestreo {fs:.2f} Hz")
        