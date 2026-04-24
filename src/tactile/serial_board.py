"""
Send commands to the Pico over USB serial (see pico/ firmware). WS2812 frames
use tactile.ws2812_serial_board; clear/reset use CLEAR and six-bit lines here.

Environment:
  PICO_SERIAL_PORT  default /dev/cu.usbmodem101 (use COMx on Windows)
  PICO_SERIAL_STARTUP_SEC  seconds after opening port (boot + main.py); default 2.5
"""

import os
import threading
import time

_ser = None
_lock = threading.Lock()


def _port():
    return os.environ.get("PICO_SERIAL_PORT", "/dev/cu.usbmodem101")


def _startup_delay():
    return float(os.environ.get("PICO_SERIAL_STARTUP_SEC", "3.0"))


def _get_serial():
    global _ser
    if _ser is not None:
        return _ser
    import serial

    try:
        # dsrdtr/rtscts False avoids some boards resetting when the port opens
        ser = serial.Serial(
            _port(),
            115200,
            timeout=0.5,
            write_timeout=2.0,
            dsrdtr=False,
            rtscts=False,
        )
    except OSError as e:
        raise OSError(
            f"Cannot open {_port()}. Close Thonny/mpremote, plug in the Pico, "
            "set PICO_SERIAL_PORT to your USB device, then reset. "
            "For WS2812, deploy pico/pico_ws2812_receiver.py as main.py; "
            "for six-GPIO Braille, use pico/serial_receiver.py as main.py."
        ) from e

    time.sleep(_startup_delay())
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception:
        pass
    # Drain any boot banner ("serial_receiver ready") from the device
    t_end = time.time() + 1.0
    while time.time() < t_end:
        n = getattr(ser, "in_waiting", 0) or 0
        if n:
            ser.read(n)
        else:
            time.sleep(0.05)

    _ser = ser
    return _ser


def _normalize_pattern(pat):
    pat = (pat or "000000") + "000000"
    out = []
    for i in range(6):
        out.append("1" if pat[i] == "1" else "0")
    return "".join(out)


def _write_line(ser, text):
    # CRLF helps some USB stacks; Pico strips \r
    data = (text + "\r\n").encode("ascii")
    ser.write(data)
    ser.flush()


def _force_leds_off(ser):
    """CLEAR plus an all-zero pattern so every pin is driven low."""
    _write_line(ser, "CLEAR")
    time.sleep(0.03)
    _write_line(ser, "000000")


def send_to_board(patterns):
    with _lock:
        ser = _get_serial()
        if not patterns:
            _force_leds_off(ser)
            if os.environ.get("SERIAL_DEBUG", "").lower() in ("1", "true", "yes"):
                print("serial -> Pico: CLEAR + 000000")
            return
        for item in patterns:
            line = _normalize_pattern(item.get("pattern", "000000"))
            _write_line(ser, line)
            if os.environ.get("SERIAL_DEBUG", "").lower() in ("1", "true", "yes"):
                print("serial -> Pico:", line)
            time.sleep(0.35)


def reset_board():
    with _lock:
        ser = _get_serial()
        _force_leds_off(ser)


def clear_board():
    with _lock:
        ser = _get_serial()
        _force_leds_off(ser)
