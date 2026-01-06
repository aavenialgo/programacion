import pandas as pd
import matplotlib.pyplot as plt

# Cargar el archivo CSV
# (cambiar la ruta por la correcta si es necesario)
df = pd.read_csv("../src/ppg_data_prueba1.csv")

# Ver las primeras filas para confirmar
print(df.head())
# Crear la figura
plt.figure(figsize=(10, 6))

# Graficar cada canal
# Tiempo (s),PPG Suavizada,Primera Derivada,Segunda Derivada (deberia ser asi)

plt.plot(df["tiempo_relativo_s"], df["Crudo"], label="Crudo", alpha=0.7)
#plt.plot(df["tiempo_relativo_s"], df["Filtrado"], label="Filtrado", alpha=0.8)
#plt.plot(df["tiempo_relativo_s"], df["Normalizado"], label="Normalizado", alpha=0.8)

# Títulos y etiquetas
plt.title("Señales PPG - Crudo / Filtrado / Normalizado")
plt.xlabel("Tiempo (s)")
plt.ylabel("Amplitud")
plt.legend()
plt.grid(True)
plt.tight_layout()

# Mostrar la gráfica
plt.show()

