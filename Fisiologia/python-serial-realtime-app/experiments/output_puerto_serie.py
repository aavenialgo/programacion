import serial

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8', errors='replace').strip()
            print(data)
except KeyboardInterrupt:
    print("Lectura detenida por el usuario.")
finally:
    ser.close()
