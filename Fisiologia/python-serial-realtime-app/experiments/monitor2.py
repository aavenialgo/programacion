
import numpy as np
import pandas as pd
import pyqtgraph as pg
from scipy.signal import butter, filtfilt


#generate layout
app = pg.mkQApp("Crosshair Example")
win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('pyqtgraph example: crosshair')
label = pg.LabelItem(justify='right')
win.addItem(label)
p1 = win.addPlot(row=1, col=0)
# customize the averaged curve that can be activated from the context menu:
p1.avgPen = pg.mkPen('#FFFFFF')
p1.avgShadowPen = pg.mkPen('#8080DD', width=10)

p2 = win.addPlot(row=2, col=0)

region = pg.LinearRegionItem()
region.setZValue(10)
# Add the LinearRegionItem to the ViewBox, but tell the ViewBox to exclude this 
# item when doing auto-range calculations.
p2.addItem(region, ignoreBounds=True)

#pg.dbg()
p1.setAutoVisible(y=True)


#create numpy arrays
#make the numbers large to show that the range shows data from 10000 to all the way 0

#lectura de archivo CSV
df = pd.read_csv('red_ir_log.csv')
print(df.head())
t = df['timestamp'].values
red = df['Red'].values
ir = df['IR'].values

def butterworth_filter(data, fs, cutoff, btype='low', order=4):
    """
    data   : señal a filtrar (array)
    fs     : frecuencia de muestreo (Hz)
    cutoff : frecuencia de corte (Hz)
    btype  : tipo de filtro ('low', 'high', 'bandpass', 'bandstop')
    order  : orden del filtro
    """
    nyq = 0.5 * fs                # frecuencia de Nyquist
    normal_cutoff = np.array(cutoff) / nyq  # normalización
    b, a = butter(order, normal_cutoff, btype=btype, analog=False)
    filtered = filtfilt(b, a, data)
    return filtered


data1 = butterworth_filter(ir, 125, cutoff=[0.5,8], btype='bandpass')
#data2 = ir
data2 = butterworth_filter(red, 125, cutoff=[0.5,8], btype='bandpass')


p1.plot(data1, pen="r") #senial ir filtrada en rojo
p1.plot(data2, pen="g") # senial red filtrada en verde

p2d = p2.plot(data2, pen="w")
# bound the LinearRegionItem to the plotted data
region.setClipItem(p2d)

def update():
    region.setZValue(10)
    minX, maxX = region.getRegion()
    p1.setXRange(minX, maxX, padding=0)    

region.sigRegionChanged.connect(update)

def updateRegion(window, viewRange):
    rgn = viewRange[0]
    region.setRegion(rgn)

p1.sigRangeChanged.connect(updateRegion)

region.setRegion([1000, 2000])

#cross hair
vLine = pg.InfiniteLine(angle=90, movable=False)
hLine = pg.InfiniteLine(angle=0, movable=False)
p1.addItem(vLine, ignoreBounds=True)
p1.addItem(hLine, ignoreBounds=True)


vb = p1.vb

def mouseMoved(evt):
    pos = evt
    if p1.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        index = int(mousePoint.x())
        if index > 0 and index < len(data1):
            label.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>,   <span style='color: green'>y2=%0.1f</span>" % (mousePoint.x(), data1[index], data2[index]))
        vLine.setPos(mousePoint.x())
        hLine.setPos(mousePoint.y())



p1.scene().sigMouseMoved.connect(mouseMoved)


if __name__ == '__main__':
    pg.exec()
