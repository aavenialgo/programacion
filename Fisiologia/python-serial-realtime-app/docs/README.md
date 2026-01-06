# PPG Analyzer - Documentación

## Estructura del Proyecto

### Directorios Principales

- **`src/`**: Código fuente principal
  - **`config/`**: Archivos de configuración
  - **`core/`**: Lógica de negocio y procesamiento
  - **`ui/`**: Interfaz de usuario
  - **`data/`**: Gestión de datos

- **`experiments/`**: Archivos de prueba y versiones legacy
- **`tests/`**: Pruebas unitarias
- **`docs/`**: Documentación del proyecto

### Próximos Pasos de Refactorización

1. **Dividir `interfaz2.py`** en módulos más pequeños  (listo)
2. **Mover lógica de procesamiento** a `src/core/processing/`
3. **Crear widgets reutilizables** en `src/ui/widgets/`
4. **Implementar pruebas unitarias** 

## Configuración

Las configuraciones principales están en:
- `src/config/settings.py` - Configuraciones generales
- `src/config/serial_config.py` - Configuración del puerto serie
- `src/config/constants.py` - Constantes del sistema

## Uso

```python
# Importar configuraciones
from src.config.settings import DEFAULT_PORT, SAMPLING_FREQUENCY
from src.config.serial_config import SerialConfig

# Obtener puertos disponibles
ports = SerialConfig.get_available_ports()
```
