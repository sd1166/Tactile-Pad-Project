import serial
import time

# On macOS use /dev/cu.* for your Pico (e.g. /dev/cu.usbmodem101)
pico = serial.Serial("/dev/cu.usbmodem101", 115200)

time.sleep(2)

pico.write(b"HELLO\n")
pico.write(b"TEST\n")

print("Sent messages")