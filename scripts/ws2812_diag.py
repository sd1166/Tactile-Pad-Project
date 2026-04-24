#!/usr/bin/env python3
"""
WS2812 + Pico USB checks. Run from the repo root:

  python scripts/ws2812_diag.py solid white
  python scripts/ws2812_diag.py stripes
  python scripts/ws2812_diag.py compare
  python scripts/ws2812_diag.py clear

Uses the same env vars as the Flask app: PICO_SERIAL_PORT,
PICO_SERIAL_STARTUP_SEC (see tactile.serial_board).

The ``compare`` command sends horizontal stripes twice: serpentine off vs on
(overrides env for that test) so you can confirm which matches your matrix.
Default app mapping uses ``WS2812_SERPENTINE`` (default **on**).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tactile.serial_board import _get_serial  # noqa: E402
from tactile.ws2812_matrix import (  # noqa: E402
    _brightness,
    panel_mapping_from_env,
    panel_strip_index,
)
from tactile.ws2812_serial_board import clear_ws2812_panel, send_ws2812_frame  # noqa: E402

W, H = 32, 8
N = W * H


def bytes_solid(rgb: tuple[int, int, int]) -> bytes:
    b = _brightness()
    r, g, colb = rgb
    return bytes(
        [
            min(255, max(0, int(round(r * b)))),
            min(255, max(0, int(round(g * b)))),
            min(255, max(0, int(round(colb * b)))),
        ]
    ) * N


def bytes_horiz_stripes(serpentine: bool | None = None) -> bytes:
    """Even logical rows white, odd black, using the same strip map as the app."""
    w = min(255, max(0, int(round(255 * _brightness()))))
    pmap = panel_mapping_from_env(serpentine)
    buf = bytearray(N * 3)
    for y in range(H):
        for x in range(W):
            idx = panel_strip_index(x, y, W, H, pmap)
            if idx is None:
                continue
            o = idx * 3
            if y % 2 == 0:
                buf[o : o + 3] = bytes([w, w, w])
            else:
                buf[o : o + 3] = bytes([0, 0, 0])
    return bytes(buf)


def drain_serial(sec: float = 2.0) -> None:
    ser = _get_serial()
    t0 = time.time()
    while time.time() - t0 < sec:
        n = getattr(ser, "in_waiting", 0) or 0
        if n:
            chunk = ser.read(n)
            sys.stdout.buffer.write(chunk)
            sys.stdout.flush()
        else:
            time.sleep(0.05)


def cmd_solid(ns: argparse.Namespace) -> None:
    colors: dict[str, tuple[int, int, int]] = {
        "off": (0, 0, 0),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
    }
    c = colors[ns.color]
    print(f"Sending solid {ns.color} to {N} LEDs ({N * 3} bytes)...")
    send_ws2812_frame(bytes_solid(c))
    print("Serial RX from Pico (2 s, look for 'frame ok bytes 768'):")
    drain_serial(2.0)
    print("\nDone.")


def cmd_stripes(_ns: argparse.Namespace) -> None:
    pmap = panel_mapping_from_env()
    print(
        "Sending horizontal even/odd row stripes "
        f"(serpentine_rows={pmap['serpentine_rows']}, same as app env)..."
    )
    send_ws2812_frame(bytes_horiz_stripes(None))
    print("Serial RX from Pico (2 s):")
    drain_serial(2.0)
    print("\nDone.")


def cmd_compare(ns: argparse.Namespace) -> None:
    pause = ns.pause
    _get_serial()
    print("Pattern A: horizontal stripes, serpentine_rows=False")
    print(f"(watch the panel for {pause:.0f} s)\n")
    send_ws2812_frame(bytes_horiz_stripes(False))
    time.sleep(pause)

    print("Pattern B: horizontal stripes, serpentine_rows=True")
    print(f"(watch the panel for {pause:.0f} s)\n")
    send_ws2812_frame(bytes_horiz_stripes(True))
    time.sleep(pause)

    clear_ws2812_panel()
    print(
        "Which pattern showed clean horizontal light/dark bands?\n"
        "  A only  -> export WS2812_SERPENTINE=0 before python app.py.\n"
        "  B only  -> default (unset WS2812_SERPENTINE) or WS2812_SERPENTINE=1.\n"
        "  neither -> tune WS2812_SWAP_AXES, FLIP_X/Y, COLUMN_MAJOR; check power, DIN, NEO_TIMING.\n"
        "Panel was cleared at the end."
    )


def cmd_clear(_ns: argparse.Namespace) -> None:
    print("Clearing panel (all pixels off)...")
    clear_ws2812_panel()
    drain_serial(1.5)
    print("Done.")


def main() -> int:
    os.chdir(ROOT)
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_solid = sub.add_parser("solid", help="Fill the whole panel with one color")
    p_solid.add_argument(
        "color",
        choices=("off", "black", "white", "red", "green", "blue"),
        help="Panel color",
    )
    p_solid.set_defaults(func=cmd_solid)

    p_stripes = sub.add_parser(
        "stripes",
        help="Even rows white, odd rows black (tests mapping)",
    )
    p_stripes.set_defaults(func=cmd_stripes)

    p_cmp = sub.add_parser(
        "compare",
        help="Show stripes twice (serpentine off then on) to match wiring",
    )
    p_cmp.add_argument(
        "-p",
        "--pause",
        type=float,
        default=6.0,
        help="Seconds to show each pattern (default 6)",
    )
    p_cmp.set_defaults(func=cmd_compare)

    p_clear = sub.add_parser("clear", help="Turn all LEDs off")
    p_clear.set_defaults(func=cmd_clear)

    ns = p.parse_args()
    try:
        ns.func(ns)
    except OSError as e:
        print(f"Serial error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
