import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
import threading

gData = []
gData.append([0])
gData.append([0])

#Configuramos la gráfica
fig = plt.figure()
ax = fig.add_subplot(111)
hl, = plt.plot(gData[0], gData[1])
plt.ylim(-90, 90)
plt.xlim(0,200)

# Función que se va a ejecutar en otro thread
# y que guardará los datos del serial en 'out_data'
def GetData(out_data):
    with serial.Serial('/dev/ttyUSB0',115200, timeout=1) as ser:
        print(ser.isOpen())
        while True:
            line = ser.readline().decode('utf-8')
        # Si la línea tiene 'Roll' la parseamos y extraemos el valor
            if "Roll" in line:
                res = re.search("Roll: ([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)", line)

        # Añadimos el nuevo valor, si hay más de 200 muestras quitamos la primera
        # para que no se nos acumulen demasiados datos en la gráfica
            out_data[1].append( float(res.group(1)) )
            if len(out_data[1]) > 200:
                out_data[1].pop(0)

# Función que actualizará los datos de la gráfica
# Se llama periódicamente desde el 'FuncAnimation'
def update_line(num, hl, data):
    hl.set_data(range(len(data[1])), data[1])
    return hl,

# Configuramos la función que "animará" nuestra gráfica
line_ani = animation.FuncAnimation(fig, update_line, fargs=(hl, gData),
    interval=50, blit=False)

# Configuramos y lanzamos el hilo encargado de leer datos del serial
dataCollector = threading.Thread(target = GetData, args=(gData,))
dataCollector.start()

plt.show()

dataCollector.join()