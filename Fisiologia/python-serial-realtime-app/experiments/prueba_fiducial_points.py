import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.signal import find_peaks

def cargar_y_procesar(path_archivo, fs=100.0):
    # 1. Lectura del archivo
    df = pd.read_csv(path_archivo)

    columnas_requeridas = {'tiempo_s', 'valor_filt'}
    faltantes = columnas_requeridas.difference(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {sorted(faltantes)}")
    
    # Extraemos las columnas específicas
    t = df['tiempo_s'].to_numpy(dtype=float)
    señal = df['valor_filt'].to_numpy(dtype=float)

    # Limpieza básica: eliminar muestras no finitas
    mascara_finita = np.isfinite(t) & np.isfinite(señal)
    if not np.all(mascara_finita):
        t = t[mascara_finita]
        señal = señal[mascara_finita]

    if len(t) < 5 or len(señal) < 5:
        raise ValueError("El archivo no tiene suficientes muestras para análisis.")
    if len(t) != len(señal):
        raise ValueError("Las columnas 'tiempo_s' y 'valor_filt' tienen longitudes distintas.")

    # Aceptar datos que comienzan en cualquier segundo (ej. 6s, 12s, etc.).
    # Solo necesitamos una base temporal ordenada y sin duplicados para derivar.
    if np.any(np.diff(t) < 0):
        orden = np.argsort(t)
        t = t[orden]
        señal = señal[orden]

    # Consolidar timestamps duplicados (muy común en adquisición por bloques)
    # usando promedio de amplitud por instante temporal.
    tiempos_unicos, inv = np.unique(t, return_inverse=True)
    if len(tiempos_unicos) < len(t):
        suma = np.bincount(inv, weights=señal)
        cuenta = np.bincount(inv)
        señal = suma / cuenta
        t = tiempos_unicos
    
    # 2. Validación temporal y configuración de fs fija
    dt_array = np.diff(t)
    if np.any(dt_array <= 0):
        raise ValueError(
            "No se pudo construir una base temporal estrictamente creciente "
            "después de limpiar/ordenar el CSV."
        )

    fs = float(fs)
    if fs <= 0:
        raise ValueError("'fs' debe ser mayor que 0.")

    # Base temporal uniforme usando el instante inicial como referencia
    t0 = float(t[0])
    t_uniforme = t0 + np.arange(len(señal)) / fs
    print(f"Frecuencia de muestreo configurada: {fs:.2f} Hz")

    # 3. Cálculo de la Primera Derivada (VPG)
    # Como fs es fija, derivamos respecto a muestras y escalamos por fs
    derivada = np.gradient(señal) * fs

    return t_uniforme, señal, derivada, fs


def detectar_fiduciales_ppg(señal, derivada, fs):
    # Detección de fiduciales sobre la PPG: S (pico), O (foot), w_ppg (máxima pendiente entre O y S)

    # 4. Detección de Puntos (S, O, w)
    mediana = np.median(señal)
    mad = np.median(np.abs(señal - mediana))
    escala_robusta = 1.4826 * mad + 1e-12

    min_distancia = max(1, int(fs * (60 / 180)))
    min_ancho = max(1, int(fs * 0.04))
    umbral_altura = mediana + 0.5 * escala_robusta
    umbral_prominencia = 0.8 * escala_robusta

    picos_s, _ = find_peaks(
        señal,
        height=umbral_altura,
        distance=min_distancia,
        prominence=umbral_prominencia,
        width=min_ancho,
    )

    if len(picos_s) == 0:
        raise RuntimeError("No se detectaron picos sistólicos con los criterios actuales.")

    # Regla fisiológica mínima: eliminar picos demasiado cercanos (> 180 lpm)
    picos_s_filtrados = [int(picos_s[0])]
    for pico in picos_s[1:]:
        if (pico - picos_s_filtrados[-1]) / fs >= (60 / 180):
            picos_s_filtrados.append(int(pico))
    picos_s = np.array(picos_s_filtrados, dtype=int)

    puntos_o = []
    puntos_w = []
    picos_s_validos = []

    for i, s in enumerate(picos_s):
        if i == 0:
            ventana_pre = int(fs * 0.30)
        else:
            rr = s - picos_s[i - 1]
            ventana_pre = int(np.clip(0.60 * rr, fs * 0.20, fs * 0.60))

        inicio = max(0, s - ventana_pre)

        segmento = señal[inicio:s]
        if len(segmento) < 3:
            continue

        # El Foot (O) es el mínimo antes del ascenso
        idx_o = np.argmin(segmento) + inicio
        if idx_o >= s - 1:
            continue
        
        # El punto w es el máximo de la derivada entre O y S
        segmento_derivada = derivada[idx_o:s]
        if len(segmento_derivada) < 2:
            continue

        idx_w = np.argmax(segmento_derivada) + idx_o

        picos_s_validos.append(int(s))
        puntos_o.append(int(idx_o))
        puntos_w.append(idx_w)

    picos_s_validos = np.array(picos_s_validos, dtype=int)
    puntos_o = np.array(puntos_o, dtype=int)
    puntos_w = np.array(puntos_w, dtype=int)

    print(
        f"Picos S detectados: {len(picos_s)} | "
        f"Latidos válidos (S-O-w): {len(picos_s_validos)} | "
        f"Descartados: {len(picos_s) - len(picos_s_validos)}"
    )

    return picos_s_validos, puntos_o, puntos_w


def detectar_fiduciales_vpg(derivada, puntos_o, picos_s):
    """
    Detecta fiduciales en VPG (primera derivada):
    - u: máximo entre O y S
    - v: mínimo entre S y siguiente O
    - w: máximo entre v y siguiente O
    """
    puntos_u = []
    puntos_v = []
    puntos_w = []

    n_latidos = min(len(puntos_o), len(picos_s))
    if n_latidos < 2:
        return np.array([], dtype=int), np.array([], dtype=int), np.array([], dtype=int)

    for i in range(n_latidos - 1):
        o_i = int(puntos_o[i])
        s_i = int(picos_s[i])
        o_sig = int(puntos_o[i + 1])

        if not (o_i < s_i < o_sig):
            continue

        seg_u = derivada[o_i:s_i]
        if len(seg_u) < 2:
            continue
        u_i = int(np.argmax(seg_u) + o_i)

        seg_v = derivada[s_i:o_sig]
        if len(seg_v) < 2:
            continue
        v_i = int(np.argmin(seg_v) + s_i)

        seg_w = derivada[v_i:o_sig]
        if len(seg_w) < 2:
            continue
        w_i = int(np.argmax(seg_w) + v_i)

        puntos_u.append(u_i)
        puntos_v.append(v_i)
        puntos_w.append(w_i)

    puntos_u = np.array(puntos_u, dtype=int)
    puntos_v = np.array(puntos_v, dtype=int)
    puntos_w = np.array(puntos_w, dtype=int)

    print(f"Fiduciales VPG -> u: {len(puntos_u)} | v: {len(puntos_v)} | w: {len(puntos_w)}")
    return puntos_u, puntos_v, puntos_w

# --- Ejecución ---
base_dir = Path(__file__).resolve().parents[1]  # raíz del proyecto
archivo = base_dir / "src" / "data" / "datos_filtrados_naza4_filtrado.csv"
FS_CONFIGURADA = 100.0
t, ppg, vpg, fs = cargar_y_procesar(str(archivo), fs=FS_CONFIGURADA)
s, o, w_ppg = detectar_fiduciales_ppg(ppg, vpg, fs)
u_vpg, v_vpg, w_vpg = detectar_fiduciales_vpg(vpg, o, s)

# 5. Visualización simultánea de PPG y VPG con sus fiduciales
fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

# PPG
axes[0].plot(t, ppg, label='PPG Filtrada', color='black', alpha=0.7)
axes[0].scatter(t[s], ppg[s], color='red', s=28, label='S (propio)')
axes[0].scatter(t[o], ppg[o], color='green', marker='x', s=40, label='O (propio)')
axes[0].scatter(t[w_ppg], ppg[w_ppg], color='blue', marker='+', s=40, label='w (PPG)')
axes[0].set_title('PPG + Fiduciales')
axes[0].set_ylabel('Amplitud')
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3)

# VPG
axes[1].plot(t, vpg, label='VPG (1ra derivada)', color='purple', alpha=0.85)
axes[1].scatter(t[u_vpg], vpg[u_vpg], color='orange', s=28, label='u (VPG)')
axes[1].scatter(t[v_vpg], vpg[v_vpg], color='brown', marker='x', s=40, label='v (VPG)')
axes[1].scatter(t[w_vpg], vpg[w_vpg], color='cyan', marker='+', s=40, label='w (VPG)')
axes[1].set_title('VPG + Fiduciales')
axes[1].set_xlabel('Tiempo (s)')
axes[1].set_ylabel('Amplitud')
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()