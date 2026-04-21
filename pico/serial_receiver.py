"""
Run on the Raspberry Pi Pico (MicroPython) as main.py so it starts on boot.

Reads lines over USB serial. Each line is either:
  - CLEAR  — turn all LEDs off
  - six characters, each 0 or 1 — set GP21,20,19,18,17,16 (dot 1 .. dot 6, BRAILLE_MAP order)

Byte-by-byte reads are more reliable than readline() on some USB stacks.
"""
from machine import Pin
import sys
from time import sleep_ms

PINS = (21, 20, 19, 18, 17, 16)
pins = [Pin(n, Pin.OUT, value=0) for n in PINS]

try:
    onboard = Pin("LED", Pin.OUT)
except Exception:
    onboard = None


def blink():
    try:
        if onboard is None:
            return
        onboard.value(1)
        sleep_ms(40)
        onboard.value(0)
    except Exception:
        pass


def read_line():
    buf = ""
    while True:
        c = sys.stdin.read(1)
        if not c:
            continue
        if c in "\r\n":
            if buf:
                return buf
            continue
        buf += c
        if len(buf) > 80:
            buf = ""


def set_pins_from_bits(bits6):
    for i in range(6):
        c = bits6[i]
        pins[i].value(1 if c == "1" else 0)


def all_off():
    for p in pins:
        p.value(0)


print("serial_receiver ready")

while True:
    line = read_line()
    line = line.strip()
    if not line:
        continue

    u = line.upper()
    if u == "CLEAR":
        all_off()
        continue

    if len(line) >= 6:
        bits = line[:6]
        if all(c in "01" for c in bits):
            set_pins_from_bits(bits)
            blink()
        # ignore malformed lines so garbage does not latch wrong outputs
