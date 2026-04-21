"""
MicroPython on Raspberry Pi Pico: drive a WS2812 panel from USB serial.

Deploy as main.py when using the 8x32 panel (default 32 wide x 8 tall, 256 LEDs).

Wiring:
  - Data in to GP15 (change PIN_DATA below if needed).
  - Common ground with the Pico.
  - WS2812 5 V power: use an adequate supply; do not power 256 LEDs from the Pico 3.3 V pin.

Protocol (ASCII, one frame per message):
  Line 1: WS2812
  Line 2: base64-encoded RGB bytes (768 bytes for 256 LEDs = width*height*3)

Also accepts the same CLEAR / 000000 lines as serial_receiver for all-off (optional).
"""
import sys
from machine import Pin

try:
    import neopixel
except ImportError:
    neopixel = None

try:
    import ubinascii
except ImportError:
    import binascii as ubinascii

PIN_DATA = 15
WIDTH = 32
HEIGHT = 8
NUM_LEDS = WIDTH * HEIGHT

_np = None


def get_np():
    global _np
    if _np is None:
        if neopixel is None:
            raise RuntimeError("neopixel module missing")
        _np = neopixel.NeoPixel(Pin(PIN_DATA), NUM_LEDS, timing=1)
    return _np


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
        if len(buf) > 1400:
            buf = ""


def apply_rgb_buffer(raw):
    np = get_np()
    n = min(NUM_LEDS, len(raw) // 3)
    for i in range(n):
        o = i * 3
        np[i] = (raw[o], raw[o + 1], raw[o + 2])
    for i in range(n, NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()


def all_off():
    np = get_np()
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()


print("ws2812_receiver ready %dx%d" % (WIDTH, HEIGHT))

while True:
    line = read_line().strip()
    if not line:
        continue
    u = line.upper()
    if u == "CLEAR":
        all_off()
        continue
    if u == "WS2812":
        b64 = read_line()
        try:
            raw = ubinascii.a2b_base64(b64.strip())
            apply_rgb_buffer(raw)
        except Exception as e:
            print("frame error:", e)
        continue
    if u == "000000":
        all_off()
        continue
