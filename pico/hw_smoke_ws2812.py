"""
Hardware smoke test for WS2812 on GP12 (no USB protocol).

Run from the repo root (Pico plugged in, Thonny closed):
  mpremote connect /dev/cu.usbmodem101 run pico/hw_smoke_ws2812.py

What you should see: LED index 0 blinks red, then green, then blue, for each
NeoPixel timing mode (1 then 0). If nothing ever lights, check 5 V, GND,
DIN on GP12, and a 3.3 V to 5 V level shifter on data if your strip needs it.
"""
from machine import Pin
from time import sleep_ms

try:
    import neopixel
except ImportError:
    print("neopixel module missing")
    raise SystemExit(1)

PIN = 12
N = 256


def main():
    for timing in (1, 0):
        print("NeoPixel timing=%d (watch first LED in the chain)" % timing)
        np = neopixel.NeoPixel(Pin(PIN), N, timing=timing)
        for i in range(N):
            np[i] = (0, 0, 0)
        for color, name in (((12, 0, 0), "red"), ((0, 12, 0), "green"), ((0, 0, 12), "blue")):
            np[0] = color
            np.write()
            print("  LED0", name)
            sleep_ms(1500)
        for i in range(N):
            np[i] = (0, 0, 0)
        np.write()
    print("Done. If LED 0 never lit, fix power/GND/DIN/timing/shifter before the web app.")


main()
