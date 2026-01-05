# PPG Analyzer - Analizador de Señales PPG en Tiempo Real

Esta aplicación es un analizador de señales fotopletismográficas (PPG) que captura datos en tiempo real desde un puerto serie, aplica filtros digitales y realiza análisis.

## Características Principales

- **Adquisición en tiempo real** - Captura datos PPG desde dispositivos serie
- **Visualización múltiple** - Gráficos de señal cruda, filtrada
- **Filtrado digital** - Filtros Butterworth configurables
- **Interfaz modular** - Arquitectura limpia y escalable
- **Exportación de datos** - Guardado en múltiples formatos

## Estructura del Proyecto

```
python-serial-realtime-app/
├── src/                              # Código fuente principal
│   ├── config/                       # Configuraciones centralizadas
│   │   ├── settings.py              # Configuraciones generales
│   │   ├── serial_config.py         # Configuración puerto serie
│   │   └── constants.py             # Constantes del sistema
│   ├── core/                        # Lógica de negocio
│   │   ├── filter.py               # Filtros digitales
│   │   ├── ppg_analisis.py         # Análisis de señales PPG
│   │   └── processing/             # Procesamiento avanzado
│   ├── ui/                          # Interfaz de usuario
│   │   ├── widgets/                # Widgets reutilizables
│   │   │   └── acquisition_controls.py
│   │   ├── styles/                 # Estilos CSS/PyQt
│   │   │   └── styles.py
│   │   ├── serial_reader.py        # Gestión puerto serie
│   │   ├── ppg_processor.py        # Procesamiento PPG
│   │   ├── acquisition_tab.py      # Pestaña adquisición
│   │   ├── interfaz2_refactored.py # App principal modular
│   │   └── interfaz2.py           # Versión original (legacy)
│   ├── data/                       # Gestión de datos
│   │   └── read_data.py
│   └── main.py                     # Punto de entrada
├── experiments/                     # Archivos experimentales
│   ├── interfaz_legacy.py         # Versión anterior
│   ├── graficador.py              # Pruebas de gráficos
│   └── monitor*.py                # Scripts de monitoreo
├── tests/                          # Pruebas unitarias
├── docs/                           # Documentación
├── requirements.txt                # Dependencias del proyecto
└── README.md                       # Este archivo
```

## Requisitos del Sistema

### Software Requerido
- **Python 3.8+** (recomendado Python 3.12)
- Sistema operativo: Linux, Windows, macOS

### Hardware Recomendado
- Dispositivo PPG con interfaz serie (USB/UART)
- Puerto USB disponible
- Mínimo 4GB RAM para procesamiento en tiempo real

## Dependencias

Este proyecto requiere las siguientes bibliotecas Python:

```
numpy>=1.21.0
matplotlib>=3.5.0
scipy>=1.7.0
pandas>=1.3.0
pyserial==3.5
PyQt5==5.15.11
PyQt5-Qt5==5.15.17
PyQt5_sip==12.17.0
pyqtgraph==0.13.7
heartpy>=1.2.0
```

### Instalación de Dependencias

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd python-serial-realtime-app
```

2. **Crear entorno virtual (recomendado):**
```bash
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

## Configuración

### Configuración del Puerto Serie

La aplicación detecta automáticamente puertos disponibles, pero puedes configurar manualmente en [`src/config/settings.py`](src/config/settings.py):

```python
DEFAULT_PORT = '/dev/ttyUSB0'  # Linux
# DEFAULT_PORT = 'COM3'        # Windows
DEFAULT_BAUD = 115200
```

### Configuración de Filtros

Ajustar parámetros de filtrado en [`src/config/settings.py`](src/config/settings.py):

```python
LOWCUT = 0.5    # Hz - Frecuencia de corte baja
HIGHCUT = 8.0   # Hz - Frecuencia de corte alta
FILTER_ORDER = 4 # Orden del filtro Butterworth
```

## Ejecución de la Aplicación

### Método Recomendado (Como Módulo)
```bash
cd python-serial-realtime-app
python -m src.main
```

### Método Alternativo
```bash
cd python-serial-realtime-app/src
python main.py
```

### Verificar Instalación
Para verificar que todos los módulos se cargan correctamente:
```bash
python -m src.test_imports
```

## Uso de la Aplicación

### 1. **Conexión del Dispositivo**
- Conecta tu dispositivo PPG al puerto USB
- La aplicación detectará automáticamente puertos disponibles

### 2. **Interfaz Principal**
La aplicación tiene dos pestañas principales:

#### **📊 Pestaña de Adquisición**
- **Panel de Control (izquierda):**
  - Selección de puerto serie y baudrate
  - Controles de conexión y adquisición
  - Estado del sistema en tiempo real
  - Log de eventos

- **Panel de Gráficos (derecha):**
  - Señal PPG cruda
  - Señal filtrada (Butterworth)
  - Señal normalizada
  - Auto-scroll para visualización continua

#### **📈 Pestaña de Análisis**
- Análisis retrospectivo de datos
- Cálculos de HRV y métricas cardiovasculares
- Exportación de resultados

### 3. **Análisis en Tiempo Real**
- **Frecuencia Cardíaca:** Calculada automáticamente cada 5 segundos
- **HRV (RMSSD):** Variabilidad de la frecuencia cardíaca
- **Calidad de Señal:** Evaluación automática de la calidad

### 4. **Formato de Datos**
La aplicación espera datos en el formato:
```
Crudo:1234,Filtrado:567,Normalizado:89
```
O simplemente valores numéricos:
```
1234.56
```

## Arquitectura del Proyecto

### Principios de Diseño
- **Modularidad:** Cada componente tiene responsabilidades específicas
- **Separación de Responsabilidades:** UI separada de lógica de negocio
- **Reutilización:** Widgets y módulos independientes
- **Escalabilidad:** Fácil agregar nuevas funcionalidades

### Módulos Principales

| Módulo | Responsabilidad |
|--------|----------------|
| [`SerialReader`](src/ui/serial_reader.py) | Comunicación con puerto serie |
| [`PPGProcessor`](src/ui/ppg_processor.py) | Procesamiento de señales PPG |
| [`AcquisitionTab`](src/ui/acquisition_tab.py) | Interfaz de adquisición |
| [`AcquisitionControls`](src/ui/widgets/acquisition_controls.py) | Widgets de control |

## Solución de Problemas

### Problemas Comunes

1. **"No se encuentran puertos serie"**
   - Verificar que el dispositivo esté conectado
   - En Linux: `ls /dev/tty*` para ver puertos disponibles
   - Verificar permisos: `sudo usermod -a -G dialout $USER`

2. **"Permission denied" en Linux**
   - Agregar usuario al grupo dialout: `sudo usermod -a -G dialout $USER`
   - Reiniciar sesión o ejecutar: `newgrp dialout`

3. **"ImportError" o problemas de módulos**
   - Verificar que todas las dependencias estén instaladas
   - Ejecutar: `python -m src.test_imports`

4. **Problemas de rendimiento**
   - Reducir frecuencia de muestreo
   - Ajustar tamaño del buffer en [`settings.py`](src/config/settings.py)

### Logs y Depuración
- Los eventos se muestran en tiempo real en el panel de log
- Errores detallados aparecen en la consola
- Verificar conexión serie antes de iniciar adquisición

## Desarrollo y Contribuciones

### Estructura para Desarrolladores

```
src/
├── config/           # Configuraciones
├── core/            # Lógica de negocio
├── ui/              # Interfaz de usuario
├── data/            # Gestión de datos
└── tests/           # Pruebas unitarias
```

### Próximas Funcionalidades


### Contribuir al Proyecto

Las contribuciones son bienvenidas! Para contribuir:

1. **Fork** el repositorio
2. **Crear rama** para nueva funcionalidad: `git checkout -b feature/nueva-funcionalidad`
3. **Commit** cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. **Push** a la rama: `git push origin feature/nueva-funcionalidad`
5. **Crear Pull Request**

### Guías de Desarrollo
- Seguir PEP 8 para estilo de código
- Documentar funciones y clases
- Agregar pruebas para nuevas funcionalidades
- Actualizar README para cambios importantes

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contacto y Soporte

- **Autor:** Andrés Venialgo
- **Repositorio:** [URL del repositorio]


**⚡ PPG Analyzer v2.0** - Análisis cardiovascular en tiempo real con arquitectura modular
