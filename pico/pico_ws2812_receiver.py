"""
MicroPython on Raspberry Pi Pico: drive a WS2812 panel from USB serial.

Deploy as main.py for a 32×8 WS2812 grid (256 LEDs), same pixel count as
Adafruit NeoMatrix(32, 8, …). Host mapping (swap / flips / column-major) is
handled in Python before frames are sent.

Wiring:
  - Data in to GP12 (change PIN_DATA below if your DIN uses another pin).
  - Common ground with the Pico.
  - WS2812 5 V power: use an adequate supply; do not power 256 LEDs from the Pico 3.3 V pin.

Protocol (ASCII, one frame per message):
  Line 1: WS2812
  Line 2: base64-encoded RGB bytes (768 bytes for 256 LEDs = width*height*3)

Also accepts the same CLEAR / 000000 lines as serial_receiver for all-off (optional).
"""
import sys
from machine import Pin
from time import sleep_ms

try:
    import neopixel
except ImportError:
    neopixel = None

try:
    import ubinascii
except ImportError:
    import binascii as ubinascii

PIN_DATA = 12
# timing=1 is usual for WS2812 / NeoPixel. If colors are wrong or nothing lights, try timing=0.
NEO_TIMING = 1
TEXT_WIDTH = 32
TEXT_HEIGHT = 8
TEXT_LEDS = TEXT_WIDTH * TEXT_HEIGHT

IMG_WIDTH = 16
IMG_HEIGHT = 16
IMG_LEDS = IMG_WIDTH * IMG_HEIGHT

NUM_LEDS = TEXT_LEDS + IMG_LEDS

# Keep False when host mapping (WS2812_FLIP_X/WS2812_FLIP_Y) is used.
FLIP_HORIZONTAL = False

_np = None

try:
    _onboard = Pin("LED", Pin.OUT)
except Exception:
    _onboard = None


def _blink_ok():
    if _onboard is None:
        return
    try:
        _onboard.value(1)
        sleep_ms(35)
        _onboard.value(0)
    except Exception:
        pass


def get_np():
    global _np
    if _np is None:
        if neopixel is None:
            raise RuntimeError("neopixel module missing")
        _np = neopixel.NeoPixel(Pin(PIN_DATA), NUM_LEDS, timing=NEO_TIMING)
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


def apply_rgb_buffer(raw, offset=0):
    np = get_np()
    n = min(NUM_LEDS, len(raw) // 3)
    for i in range(n):
        o = i * 3
        r, g, b = raw[o], raw[o + 1], raw[o + 2]
        if FLIP_HORIZONTAL:
            y = i // TEXT_WIDTH
            x = i % TEXT_WIDTH
            dst_i = y * TEXT_WIDTH + (TEXT_WIDTH - 1 - x + offset)
        else:
            dst_i = i + offset
        np[dst_i] = (r, g, b)
    for i in range(n, TEXT_LEDS):
        np[i + offset] = (0, 0, 0)
    np.write()


def all_off():
    np = get_np()
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()


print("ws2812_receiver ready %dx%d" % (TEXT_WIDTH, TEXT_HEIGHT))

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
            frame_offset = 0
            if b64.startswith("IMAGE"):
                b64 = read_line()
                frame_offset = TEXT_LEDS
            raw = ubinascii.a2b_base64(b64.strip())
            apply_rgb_buffer(raw, offset=frame_offset)
            print("frame ok bytes", len(raw))
            _blink_ok()
        except Exception as e:
            print("frame error:", e)
        continue
    if u == "000000":
        all_off()
        continue
