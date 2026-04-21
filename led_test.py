"""
Quick hardware check: each of GP16–GP21 goes high in turn, then all on, then off.
Run on the Pico: mpremote run led_test.py
Wire: GPIO -> resistor (~220 Ω) -> LED + -> LED - -> GND.
"""
from machine import Pin
from time import sleep_ms

PINS = (16, 17, 18, 19, 20, 21)
leds = [Pin(n, Pin.OUT, value=0) for n in PINS]

print("LED test: one pin at a time (1 s each)")
for i, led in enumerate(leds):
    led.value(1)
    print("GP%d ON" % PINS[i])
    sleep_ms(1000)
    led.value(0)

print("All ON 2 s")
for led in leds:
    led.value(1)
sleep_ms(2000)

print("All OFF")
for led in leds:
    led.value(0)

print("Done.")
