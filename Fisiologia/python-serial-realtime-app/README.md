# Python Serial Real-Time Application

Este proyecto es una aplicación en Python que lee datos del puerto serie `/dev/ttyUSB0`, aplica un filtro Butterworth a los datos y los grafica en tiempo real. 

## Estructura del Proyecto

```
python-serial-realtime-app
├──pruebas
    ├── output_puerto_serie.py #prueba para leer puerto serie
    ├──
├── src
│   ├── main.py          # Punto de entrada de la aplicación
│   ├── filter.py        # Contiene las funciones de filtrado
│   └── types
│       └── __init__.py  # Paquete para definiciones de tipos
├── requirements.txt     # Dependencias del proyecto
└── README.md            # Documentación del proyecto
```

## Requisitos

Asegúrate de tener Python 3 instalado en tu sistema. Este proyecto requiere las siguientes bibliotecas:

- numpy
- matplotlib
- scipy
- pyserial
- PyQt5==5.15.11
- PyQt5-Qt5==5.15.17
- PyQt5_sip==12.17.0
- pyqtgraph==0.13.7
- pyserial==3.5

Puedes instalar las dependencias utilizando el siguiente comando:

```
pip install -r requirements.txt
```

## Ejecución

Para ejecutar la aplicación, utiliza el siguiente comando:

```
python src/main.py
```

Asegúrate de que el dispositivo esté conectado al puerto serie `/dev/ttyUSB0` antes de ejecutar la aplicación. La aplicación comenzará a leer datos del puerto serie y graficará los resultados en tiempo real.

## Contribuciones

Las contribuciones son bienvenidas. Si deseas mejorar este proyecto, siéntete libre de abrir un issue o un pull request.
