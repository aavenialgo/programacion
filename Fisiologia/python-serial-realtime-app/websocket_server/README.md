# 🌐 WebSocket Server - Visualización PPG en Tiempo Real

Servidor WebSocket independiente para visualización de señales fotopletismográficas (PPG) en tiempo real a través de WiFi, con dashboard científico responsive y sistema de monitoreo de calidad de transmisión.

## 📋 Características Principales

- 🔌 **Lectura directa del puerto serial** - Opera de forma independiente
- 🔗 **Integración con Tkinter** - Recibe datos de la aplicación existente
- 📊 **Dashboard científico** - Visualización con Plotly.js (zoom, pan nativos)
- 🎛️ **Filtros Butterworth configurables** - Control en tiempo real de parámetros
- 🔐 **Autenticación por contraseña** - Acceso seguro al servidor
- 📡 **Soporte multi-cliente** - Hasta 4 clientes simultáneos
- 📈 **Monitoreo de calidad** - Detección de pérdidas, latencia, jitter
- 📱 **Responsive design** - Optimizado para móvil, tablet y desktop
- 💾 **Gestión de datos** - Exportar/importar CSV para análisis offline

## 🏗️ Arquitectura

### Sistema Híbrido

El servidor puede operar en tres modos:

```
Modo Serial (independiente):
Puerto Serial → Servidor WebSocket → Clientes (3-4 simultáneos)

Modo Tkinter (integrado):
App Tkinter → HTTP POST → Servidor WebSocket → Clientes

Modo Auto:
Intenta Serial primero, fallback a Tkinter
```

### Estructura de Archivos

```
websocket_server/
├── server.py              # FastAPI + WebSocket server
├── serial_reader.py       # Lectura del puerto serial
├── signal_processor.py    # Filtros Butterworth con scipy
├── auth_manager.py        # Sistema de autenticación
├── quality_monitor.py     # Monitoreo de calidad
├── config.py              # Configuración centralizada
├── requirements.txt       # Dependencias Python
├── README.md              # Este archivo
└── static/
    ├── index.html         # Dashboard principal
    ├── diagnostics.html   # Página de diagnóstico
    ├── app.js             # Lógica del cliente
    ├── quality.js         # Cliente de diagnóstico
    └── style.css          # Estilos responsive
```

## 🚀 Instalación

### 1. Requisitos del Sistema

- **Python 3.8+** (recomendado Python 3.10 o superior)
- Sistema operativo: Windows, Linux, macOS
- Navegador web moderno (Chrome, Firefox, Safari, Edge)

### 2. Instalar Dependencias

```bash
# Navegar al directorio del servidor
cd Fisiologia/python-serial-realtime-app/websocket_server

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias Principales

- `fastapi` - Framework web asíncrono
- `uvicorn` - Servidor ASGI
- `websockets` - Protocolo WebSocket
- `numpy` - Procesamiento numérico
- `scipy` - Filtros digitales
- `pyserial` - Comunicación serial

## ⚙️ Configuración

### Archivo `config.py`

Edite `config.py` para personalizar el comportamiento del servidor:

```python
# Puerto Serial
SERIAL_PORT = "COM3"  # Windows: "COM3", Linux: "/dev/ttyUSB0"
BAUD_RATE = 115200
SAMPLE_RATE = 100  # Hz

# Servidor WebSocket
WS_HOST = "0.0.0.0"  # Accesible en toda la red local
WS_PORT = 8765
PASSWORD = "cambiar123"  # ⚠️ CAMBIAR EN PRODUCCIÓN

# Filtro Butterworth
DEFAULT_FILTER_LOW = 0.5   # Hz
DEFAULT_FILTER_HIGH = 45.0  # Hz
DEFAULT_FILTER_ORDER = 4

# Visualización
DEFAULT_WINDOW_SECONDS = 10
MAX_CLIENTS = 4

# Modo de operación
DATA_SOURCE_MODE = "auto"  # "serial", "tkinter", o "auto"
```

### Variables de Entorno (Opcional)

Puede configurar usando variables de entorno:

```bash
export SERIAL_PORT="/dev/ttyUSB0"
export WS_PORT=8765
export WS_PASSWORD="mi_password_seguro"
export DATA_SOURCE_MODE="serial"
```

## 🏃 Ejecución

### Modo Independiente (Puerto Serial)

```bash
# Asegúrese de que el dispositivo PPG esté conectado
# Ejecutar el servidor
python server.py
```

El servidor iniciará en `http://localhost:8765`

### Modo Integrado (con Tkinter)

1. Configure `DATA_SOURCE_MODE = "tkinter"` en `config.py`
2. Ejecute el servidor WebSocket
3. Ejecute la aplicación Tkinter existente

La aplicación Tkinter puede enviar datos mediante:

```python
import requests

# Enviar datos al servidor WebSocket
requests.post('http://localhost:8765/data/push', json={
    'timestamp': 1.234,
    'value': -67980.0
})
```

### Verificar el Servidor

Abra su navegador en:
- **Dashboard principal**: `http://localhost:8765`
- **Diagnóstico**: `http://localhost:8765/diagnostics`

## 📱 Acceso desde Dispositivos Móviles

### 1. Encontrar la IP del Servidor

**Windows:**
```cmd
ipconfig
```
Busque "Dirección IPv4" (ej: `192.168.1.100`)

**Linux/Mac:**
```bash
ifconfig
# o
ip addr show
```
Busque la IP de su interfaz de red (ej: `192.168.1.100`)

### 2. Conectar desde Móvil

En el navegador del dispositivo móvil:
```
http://192.168.1.100:8765
```

⚠️ **Importante**: El servidor y el dispositivo móvil deben estar en la misma red WiFi.

## 🎮 Uso del Dashboard

### 1. Autenticación

1. Ingrese la contraseña configurada en `config.py`
2. Haga clic en "Conectar"
3. El dashboard se habilitará al autenticarse

### 2. Panel de Control

#### **Filtros Butterworth**
- ✅ **Toggle ON/OFF**: Activar/desactivar filtrado
- ⚙️ **Frecuencia Baja**: Frecuencia de corte inferior (Hz)
- ⚙️ **Frecuencia Alta**: Frecuencia de corte superior (Hz)
- ⚙️ **Orden**: Orden del filtro (1-10)
- 🔄 **Actualizar**: Aplicar cambios al filtro
- 👁️ **Ver Señal**: Seleccionar cruda, filtrada o ambas

#### **Controles de Visualización**
- ⏸️ **Play/Pausa**: Pausar/reanudar visualización
- 📏 **Ventana**: Segundos de señal mostrados (1-60s)
- 📊 **Auto-escala Y**: Ajuste automático del eje vertical

#### **Gestión de Datos**
- 💾 **Guardar CSV**: Exportar datos capturados
- 📂 **Cargar CSV**: Importar datos para análisis offline

### 3. Gráfico Interactivo (Plotly.js)

- 🔍 **Zoom**: Arrastrar para hacer zoom en región
- 🖱️ **Pan**: Arrastrar para desplazar
- 🏠 **Reset**: Doble clic para restaurar vista
- 📷 **Captura**: Botón de cámara para guardar imagen

### 4. Monitoreo de Calidad

**Indicadores en tiempo real:**
- 🟢 Verde: < 1% pérdida (Excelente)
- 🟡 Amarillo: 1-5% pérdida (Buena)
- 🔴 Rojo: > 5% pérdida (Deficiente)

**Métricas:**
- Tasa de pérdida de paquetes (%)
- Latencia promedio (ms)
- Paquetes recibidos

**Diagnóstico completo:**
- Clic en "Diagnóstico Completo" abre ventana detallada
- Historial de 60 segundos
- Recomendaciones automáticas
- Exportación de reportes

## 📊 Formato de Datos

### Datos del Serial

El servidor soporta múltiples formatos:

**Formato recomendado (CSV):**
```
1.3249752521514893,-67980.0
1.334998607635498,-68056.0
```

**Formato legacy (Tkinter):**
```
Crudo:-67980.0,Filtrado:-67950.5,Normalizado:89.2
```

**Valores simples:**
```
-67980.0
-68056.0
```

### Mensaje WebSocket (JSON)

El servidor transmite datos en formato:

```json
{
  "seq": 12345,
  "timestamp": 1.3249752521514893,
  "raw": -67980.0,
  "filtered": -67950.5,
  "server_time": 1643234567.123
}
```

- `seq`: Número de secuencia (para detectar pérdidas)
- `timestamp`: Tiempo relativo en segundos
- `raw`: Valor crudo de la señal
- `filtered`: Valor filtrado
- `server_time`: Timestamp del servidor (Unix time)

## 🔧 API REST

### Endpoints Disponibles

#### `POST /auth`
Autenticación con contraseña.

**Request:**
```json
{
  "password": "cambiar123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "token_aleatorio_seguro"
}
```

#### `GET /filter/config`
Obtener configuración actual del filtro.

**Response:**
```json
{
  "enabled": true,
  "lowcut": 0.5,
  "highcut": 45.0,
  "order": 4,
  "sample_rate": 100
}
```

#### `POST /filter/config`
Configurar parámetros del filtro.

**Request:**
```json
{
  "enabled": true,
  "lowcut": 0.5,
  "highcut": 45.0,
  "order": 4
}
```

#### `POST /data/push`
Enviar datos desde Tkinter (modo integrado).

**Request:**
```json
{
  "timestamp": 1.234,
  "value": -67980.0
}
```

#### `POST /data/upload`
Subir archivo CSV para análisis offline.

**Form Data:**
- `file`: Archivo CSV

#### `GET /quality/stats`
Obtener estadísticas de calidad de todos los clientes.

#### `GET /status`
Estado general del servidor.

## 🔗 Integración con App Tkinter Existente

### Opción 1: Envío HTTP (Recomendado)

Agregar al código Tkinter:

```python
import requests
import threading

class TkinterIntegration:
    def __init__(self, server_url="http://localhost:8765"):
        self.server_url = server_url
        
    def send_data(self, timestamp, value):
        """Envía datos al servidor WebSocket de forma asíncrona"""
        def _send():
            try:
                requests.post(
                    f"{self.server_url}/data/push",
                    json={"timestamp": timestamp, "value": value},
                    timeout=0.1
                )
            except:
                pass  # Ignorar errores de red
        
        # Enviar en hilo separado para no bloquear UI
        threading.Thread(target=_send, daemon=True).start()

# Uso en el código existente
integration = TkinterIntegration()

# Cuando se reciben datos del serial
def on_serial_data(timestamp, value):
    # ... procesamiento existente ...
    
    # Enviar al servidor WebSocket
    integration.send_data(timestamp, value)
```

### Opción 2: Configurar Modo Serial

Si el servidor WebSocket lee directamente del puerto serial, configure:

```python
# En config.py
DATA_SOURCE_MODE = "serial"
SERIAL_PORT = "COM3"  # El mismo puerto que usa Tkinter
```

⚠️ **Nota**: Solo uno puede usar el puerto serial a la vez. Use Opción 1 si Tkinter ya usa el puerto.

## 🧪 Testing y Diagnóstico

### Test de Conectividad

```bash
# Verificar que el servidor esté corriendo
curl http://localhost:8765/status
```

### Test de Autenticación

```bash
curl -X POST http://localhost:8765/auth \
  -H "Content-Type: application/json" \
  -d '{"password": "cambiar123"}'
```

### Listar Puertos Seriales Disponibles

```python
from serial_reader import SerialReader

ports = SerialReader.list_ports()
for port in ports:
    print(f"{port['device']}: {port['description']}")
```

### Simular Datos de Prueba

```python
# Modificar server.py para generar datos sintéticos
import asyncio
import numpy as np

async def generate_test_data():
    """Genera señal sintética para pruebas"""
    t = 0
    while True:
        # Señal seno + ruido
        value = np.sin(2 * np.pi * 1.0 * t) + 0.1 * np.random.randn()
        await state.process_and_broadcast(t, value)
        t += 0.01  # 100 Hz
        await asyncio.sleep(0.01)

# Iniciar en startup_event()
```

## 🛠️ Troubleshooting

### Problema: "Puerto serial en uso"

**Solución:**
1. Cerrar la app Tkinter si está usando el puerto
2. Verificar que ningún otro programa use el puerto
3. En Windows, verificar Device Manager
4. Usar modo "tkinter" si Tkinter controla el puerto

### Problema: "No se puede conectar desde móvil"

**Solución:**
1. Verificar que ambos estén en la misma red WiFi
2. Desactivar firewall temporalmente
3. Verificar que `WS_HOST = "0.0.0.0"` en config.py
4. En Linux, permitir el puerto:
   ```bash
   sudo ufw allow 8765
   ```

### Problema: "Alta pérdida de paquetes"

**Solución:**
1. Reducir ventana de visualización (menos segundos)
2. Cerrar otras aplicaciones que usen red
3. Usar conexión Ethernet en lugar de WiFi
4. Reducir frecuencia de muestreo si es posible

### Problema: "Filtro no funciona correctamente"

**Solución:**
1. Verificar que frecuencias de corte sean válidas:
   - `lowcut < highcut`
   - `highcut < sample_rate / 2` (criterio de Nyquist)
2. Aumentar orden del filtro (4-8 recomendado)
3. Verificar que hay suficientes datos (mínimo 3 × orden)

### Problema: "WebSocket se desconecta"

**Solución:**
1. Verificar que el token no haya expirado (24h por defecto)
2. Revisar logs del servidor en terminal
3. Verificar estabilidad de la red
4. Reducir número de clientes conectados

## 📈 Optimización de Rendimiento

### Para Redes Lentas

```python
# En config.py
SAMPLE_RATE = 50  # Reducir de 100 Hz a 50 Hz
DEFAULT_WINDOW_SECONDS = 5  # Ventana más pequeña
BUFFER_SIZE = 500  # Buffer más pequeño
```

### Para Muchos Clientes

```python
MAX_CLIENTS = 8  # Aumentar límite
```

⚠️ Cada cliente adicional aumenta la carga del servidor.

### Para Análisis Científico

```python
# Aumentar orden del filtro para mejor calidad
DEFAULT_FILTER_ORDER = 8
BUFFER_SIZE = 10000  # Buffer más grande
```

## 🔐 Seguridad

### Cambiar Contraseña

```python
# En config.py
PASSWORD = "mi_password_muy_seguro_123"

# O usar variable de entorno
# export WS_PASSWORD="mi_password_muy_seguro_123"
```

### HTTPS (Producción)

Para usar en producción con HTTPS:

```bash
# Generar certificados SSL
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Ejecutar con SSL
uvicorn server:app \
  --host 0.0.0.0 \
  --port 8765 \
  --ssl-keyfile key.pem \
  --ssl-certfile cert.pem
```

## 📚 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Plotly.js Documentation](https://plotly.com/javascript/)
- [Scipy Signal Processing](https://docs.scipy.org/doc/scipy/reference/signal.html)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## 📝 Licencia

Este proyecto está bajo la misma licencia que el proyecto principal.

## 👥 Contribuciones

Contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crear rama de feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📧 Soporte

Para problemas o preguntas:
- Abrir un issue en GitHub
- Revisar la sección de Troubleshooting
- Consultar la documentación de la app principal

---

**Desarrollado con ❤️ para el proyecto de Fisiología**
