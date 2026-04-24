"""
Send a full WS2812 frame to the Pico over USB (base64-encoded RGB).

Reuses the same USB serial connection and lock as tactile.serial_board so you do not
open the port twice. Import serial_board before this module (or call any
serial_board function once first) so the port is configured.
"""

import base64
import os
import time

from tactile.serial_board import _get_serial, _lock


def send_ws2812_frame(rgb_bytes):
    """Send one frame: WS2812\\n + base64 + \\n"""
    if len(rgb_bytes) % 3 != 0:
        raise ValueError("RGB buffer length must be multiple of 3")
    b64 = base64.b64encode(rgb_bytes).decode("ascii")
    with _lock:
        ser = _get_serial()
        line = "WS2812\n" + b64 + "\n"
        ser.write(line.encode("ascii"))
        ser.flush()
        # Let the Pico finish decoding and driving the strip before the next command.
        time.sleep(float(os.environ.get("WS2812_POST_WRITE_DELAY_SEC", "0.06")))
        if os.environ.get("SERIAL_DEBUG", "").lower() in ("1", "true", "yes"):
            print("serial -> Pico: WS2812 frame", len(rgb_bytes) // 3, "LEDs")


def clear_ws2812_panel(num_leds=256):
    send_ws2812_frame(bytes(num_leds * 3))
