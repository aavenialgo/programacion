# 🚀 Quick Start Guide - WebSocket PPG Server

Esta guía te ayudará a poner en marcha el servidor WebSocket en menos de 5 minutos.

## ⚡ Inicio Rápido

### 1. Instalación (2 minutos)

```bash
# Navegar al directorio del servidor
cd Fisiologia/python-serial-realtime-app/websocket_server

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración Básica (1 minuto)

Edita `config.py` o crea un archivo `.env`:

```bash
# Cambiar la contraseña (IMPORTANTE)
export WS_PASSWORD="mi_password_seguro"

# Opcional: Configurar puerto serial
export SERIAL_PORT="/dev/ttyUSB0"  # Linux/Mac
# export SERIAL_PORT="COM3"         # Windows
```

### 3. Verificar Instalación (30 segundos)

```bash
python test_websocket.py
```

Deberías ver:
```
✅ Signal Processor: PASS
✅ Authentication Manager: PASS
✅ Quality Monitor: PASS
✅ Integration: PASS
Total: 4/4 tests passed
```

### 4. Iniciar Servidor (30 segundos)

```bash
python server.py
```

Verás:
```
INFO:     Servidor listo en http://0.0.0.0:8765
```

### 5. Acceder al Dashboard (30 segundos)

1. Abre tu navegador
2. Ve a: http://localhost:8765
3. Ingresa la contraseña configurada
4. ¡Listo! 🎉

## 📱 Acceso desde Móvil

### Encontrar IP del servidor:

**Windows:**
```cmd
ipconfig
```

**Linux/Mac:**
```bash
hostname -I
# o
ifconfig
```

### Conectar desde móvil:

1. Asegúrate de estar en la misma red WiFi
2. Abre el navegador del móvil
3. Ve a: `http://192.168.1.XXX:8765` (usa tu IP)
4. Ingresa contraseña

## 🔧 Modos de Operación

### Modo 1: Independiente (Sin Tkinter)

El servidor lee directamente del puerto serial:

```python
# En config.py
DATA_SOURCE_MODE = "serial"
SERIAL_PORT = "/dev/ttyUSB0"
```

### Modo 2: Integrado (Con Tkinter)

El servidor recibe datos de la app Tkinter:

```python
# En config.py
DATA_SOURCE_MODE = "tkinter"
```

Agregar a tu código Tkinter:
```python
from tkinter_integration import TkinterWebSocketBridge

bridge = TkinterWebSocketBridge()

# En tu callback de datos:
def on_data(timestamp, value):
    # Tu código...
    bridge.send_data(timestamp, value)
```

### Modo 3: Auto (Recomendado)

Intenta serial primero, luego Tkinter:

```python
# En config.py (por defecto)
DATA_SOURCE_MODE = "auto"
```

## 🎛️ Uso del Dashboard

### 1. Autenticación
- Ingresa la contraseña
- Clic en "Conectar"

### 2. Visualización
- **Play/Pausa**: Control de actualización
- **Ventana**: Ajusta segundos mostrados
- **Señal**: Elige ver cruda, filtrada o ambas

### 3. Filtros
- Activa/desactiva filtro
- Ajusta frecuencias de corte
- Cambia orden del filtro
- Clic en "Actualizar"

### 4. Gestión de Datos
- **Guardar CSV**: Exporta datos capturados
- **Cargar CSV**: Analiza datos offline

### 5. Calidad
- Indicador de color en tiempo real
- Clic en "Diagnóstico" para detalles

## 📊 Cargar Datos de Ejemplo

El test suite generó `sample_data.csv`:

1. Clic en "Cargar CSV"
2. Selecciona `sample_data.csv`
3. Clic en "Cargar"
4. ¡Verás 30 segundos de señal sintética!

## 🐛 Problemas Comunes

### "Puerto serial en uso"

**Solución**: Usar modo Tkinter o cerrar otro programa usando el puerto.

```python
DATA_SOURCE_MODE = "tkinter"
```

### "No puedo conectar desde móvil"

**Solución**: Verificar firewall y que ambos estén en la misma WiFi.

```bash
# Linux
sudo ufw allow 8765

# Windows
# Firewall → Permitir app → Puerto 8765
```

### "Contraseña incorrecta"

**Solución**: Verificar que usas la misma contraseña que en `config.py`.

```python
# En config.py
PASSWORD = "cambiar123"  # Debe coincidir con la que ingresas
```

### "Pérdida de paquetes alta"

**Soluciones**:
- Cerrar otras apps usando la red
- Usar Ethernet en lugar de WiFi
- Reducir ventana de visualización
- Acercarse al router WiFi

## 📖 Más Información

- **README.md**: Documentación completa
- **test_websocket.py**: Ejemplos de código
- **tkinter_integration.py**: Integración con Tkinter
- **config.py**: Todas las opciones configurables

## 🎓 Tutoriales Rápidos

### Tutorial 1: Visualizar Datos Sintéticos

```bash
# 1. Iniciar servidor
python server.py

# 2. En otro terminal, generar datos de prueba
python -c "
import requests
import time
import numpy as np

for i in range(100):
    t = i * 0.01
    v = 1000 * np.sin(2 * np.pi * 1.0 * t)
    requests.post('http://localhost:8765/data/push', 
                  json={'timestamp': t, 'value': v})
    time.sleep(0.01)
"
```

### Tutorial 2: Cambiar Parámetros del Filtro

```bash
curl -X POST http://localhost:8765/filter/config \
  -H "Content-Type: application/json" \
  -d '{
    "lowcut": 0.5,
    "highcut": 10.0,
    "order": 6,
    "enabled": true
  }'
```

### Tutorial 3: Ver Estadísticas de Calidad

```bash
curl http://localhost:8765/quality/stats | python -m json.tool
```

## 💡 Tips y Trucos

### Tip 1: Mejor Rendimiento
- Usa conexión Ethernet en lugar de WiFi
- Cierra pestañas innecesarias del navegador
- Reduce ventana de visualización (5-10 segundos)

### Tip 2: Análisis Científico
- Aumenta orden del filtro a 8 para mejor calidad
- Usa ventanas de 30 segundos para análisis largo
- Exporta datos para procesamiento con Python/MATLAB

### Tip 3: Múltiples Dispositivos
- Abre el dashboard en varios dispositivos
- Hasta 4 clientes simultáneos soportados
- Cada uno puede tener configuración de vista diferente

### Tip 4: Seguridad
- Cambia la contraseña por defecto
- Usa HTTPS en producción (ver README.md)
- No compartas tu token de sesión

## 🎯 Casos de Uso

### Caso 1: Demostración en Clase
1. Conecta dispositivo PPG
2. Inicia servidor en laptop
3. Estudiantes abren dashboard en sus móviles
4. Todos ven la señal en tiempo real

### Caso 2: Experimento Remoto
1. Servidor corre en laboratorio
2. Investigadores acceden remotamente
3. Monitorean calidad de señal
4. Exportan datos para análisis

### Caso 3: Desarrollo y Debug
1. Usa datos sintéticos con `sample_data.csv`
2. Prueba diferentes configuraciones de filtro
3. Verifica calidad de transmisión
4. Optimiza parámetros

## 🆘 Soporte

¿Problemas? Revisa:
1. `README.md` - Sección de troubleshooting
2. `test_websocket.py` - Tests y ejemplos
3. Logs del servidor en la terminal
4. Issues en GitHub

## ✅ Checklist de Inicio

- [ ] Dependencias instaladas
- [ ] Tests ejecutados exitosamente
- [ ] Contraseña cambiada
- [ ] Servidor iniciado sin errores
- [ ] Dashboard accesible en navegador
- [ ] Autenticación funcionando
- [ ] Datos visualizándose (reales o sintéticos)
- [ ] Filtros configurables
- [ ] Calidad monitoreada
- [ ] Acceso desde móvil probado (opcional)

## 🎉 ¡Listo!

Ya tienes el servidor WebSocket funcionando. Disfruta de la visualización en tiempo real de tus señales PPG.

Para más información, consulta el README.md completo.

---

**Desarrollado con ❤️ para el proyecto de Fisiología**
