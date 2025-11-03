import numpy as np

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Genera una gráfica de una función gaussiana y su transformada de Fourier (numérica y analítica)

import matplotlib.pyplot as plt

def gaussian(t, sigma):
    return np.exp(-t**2 / (2 * sigma**2))



def main():
    # Parámetros de muestreo y señal
    N = 4096             # número de puntos (potencia de 2 recomendable)
    dt = 5e-4            # intervalo de muestreo (segundos)
    t = (np.arange(N) - N/2) * dt  # eje temporal centrado en cero

    sigma = 0.03         # ancho de la gaussiana (segundos)
    g = gaussian(t, sigma)

    # Transformada de Fourier numérica (escalada para aproximar la FT continua)
    # Usamos ifftshift antes del FFT porque la señal está centrada en t=0
    G_num = dt * np.fft.fftshift(np.fft.fft(np.fft.ifftshift(g)))
    f = np.fft.fftshift(np.fft.fftfreq(N, d=dt))  # eje de frecuencias en Hz

    # Gráficas
    fig, axes = plt.subplots(2, 1, figsize=(8, 6))
    axes[0].plot(t, g, color='C0')
    axes[0].set_xlim(t.min(), t.max())
    axes[0].set_xlabel('Tiempo (s)')
    axes[0].set_ylabel('Amplitud')
    axes[0].set_title('Gaussiana en el dominio del tiempo')
    axes[0].grid(True)

    axes[1].plot(f, np.abs(G_num), label='FT numérica (|G|)', color='C1')
    axes[1].set_xlim(-200, 200)  # ajustar según sigma para ver la forma principal
    axes[1].set_xlabel('Frecuencia (Hz)')
    axes[1].set_ylabel('Magnitud')
    axes[1].set_title('Transformada de Fourier')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()