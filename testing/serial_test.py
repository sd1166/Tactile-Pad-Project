import serial
import time

pico = serial.Serial('/dev/tty.usbmodem101', 115200)

time.sleep(2)

pico.write(b"HELLO\n")
pico.write(b"TEST\n")

print("Sent messages")