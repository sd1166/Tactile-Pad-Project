# Tactile

## Build

Requires Python 3.10+. From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

(or `python -m tactile`)

The app expects a Pico on USB with `PICO_SERIAL_PORT` if the default device is wrong.

## WS2812 panel (Display)

Flash `pico/pico_ws2812_receiver.py` as `main.py` on the Pico. Data in to **GP12** (edit `PIN_DATA` in that file if your DIN uses another pin). Use a solid **5 V** supply for the matrix; common ground with the Pico.

**Reference panel:** the same **32×8** class as Adafruit `NeoMatrix(32, 8, PIN, NEO_MATRIX_BOTTOM + NEO_MATRIX_RIGHT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG, NEO_GRB + NEO_KHZ800)`. This repo’s **defaults** match the **layout** part of that line (not the pin or color flags):

| Adafruit | Env (default in parentheses) |
|----------|------------------------------|
| `32`, `8` | Logical grid 32×8 (fixed in host + Pico frame size) |
| `NEO_MATRIX_COLUMNS` | **`WS2812_COLUMN_MAJOR=1`** (default **on**) |
| `NEO_MATRIX_ZIGZAG` | **`WS2812_SERPENTINE=1`** (default **on**) |
| Native 32×8 strip order (not treating the chain as 8×32) | **`WS2812_SWAP_AXES=0`** (default **off**) |
| `NEO_MATRIX_BOTTOM` + `NEO_MATRIX_RIGHT` | Tune **`WS2812_FLIP_X`** / **`WS2812_FLIP_Y`** until a letter and `ws2812_diag.py compare` look correct (no single env line equals both flags) |
| `NEO_GRB` | MicroPython `neopixel` on the Pico usually matches WS2812 **GRB** when you set `(R, G, B)` tuples; if red and green swap, fix in firmware or host byte order |

**Strip layout (env):**

- **`WS2812_SWAP_AXES`** (default **off**): **on** (`1`) when the physical chain is wired as **8×32** but you still draw **32×8** Braille; maps logical `(x,y)` to `(y,x)` on an 8×32 index grid. **off** matches **`NeoMatrix(32, 8, …)`**-style **32×8** order.
- **`WS2812_COLUMN_MAJOR`** (default **on**): column-first strip order (same idea as **`NEO_MATRIX_COLUMNS`**). Set to **`0`** for row-major panels.
- **`WS2812_SERPENTINE`** (default **on**): zig-zag along the active dimension (columns when column-major). Set **`0`** if `ws2812_diag.py compare` pattern A only looks right.
- **`WS2812_FLIP_X`**, **`WS2812_FLIP_Y`** (default **off** / **on**): mirror in strip space after swap. Adjust if text is mirrored or upside down relative to your DIN corner.

### Connection and wiring checks

From the repo root (with the Pico unplugged from Thonny and `PICO_SERIAL_PORT` set if needed):

```bash
python scripts/ws2812_diag.py solid red
python scripts/ws2812_diag.py compare
python scripts/ws2812_diag.py clear
```

`solid red` (or `white`) proves USB + firmware are receiving frames. If the Pico runs `pico_ws2812_receiver.py`, you should also see **`frame ok bytes 768`** in the script output when the Pico prints to USB. **`compare`** shows horizontal stripes twice (serpentine off, then on) so you can pick **`WS2812_SERPENTINE`**; **`stripes`** uses the same mapping as the running app (including env).

### Nothing lights up

- **One letter** (for example `a`) only turns on **one** LED at the top-left of the logical grid. It is easy to miss or to land on a dead pixel; try a short word like `hello`.
- If horizontal bands from `ws2812_diag.py compare` look broken, use the script’s A/B hint for `WS2812_SERPENTINE`, then adjust `WS2812_SWAP_AXES`, `WS2812_FLIP_X`, `WS2812_FLIP_Y`, and `WS2812_COLUMN_MAJOR` (see above).
- If the Pico’s **green LED blinks** after each Display, the frame was received; the issue is then wiring, power, data pin, or `NEO_TIMING` in `pico_ws2812_receiver.py` (try `NEO_TIMING = 0`).
- Optional env: `WS2812_MARGIN_X`, `WS2812_MARGIN_Y` shift the pattern (pixels). `PICO_SERIAL_STARTUP_SEC` (default 3) waits after opening USB. `WS2812_POST_WRITE_DELAY_SEC` (default 0.06) pauses after each frame.
- **`WS2812_BRIGHTNESS`** (default `0.25`): scale for lit Braille pixels and `ws2812_diag` solids (0.0–1.0). Use `1.0` for full brightness.

### `frame ok bytes 768` but the matrix stays dark

Software and USB are fine; the problem is between **GP12** (or whatever `PIN_DATA` is) and the first LED.

1. **Power**  
   - **5 V** and **GND** from a supply that can deliver enough current for the whole matrix (not from the Pico 3.3 V pin).  
   - **Common ground**: strip GND must connect to **Pico GND** (same supply return path).

2. **Data wire**  
   - Panel **DIN** (first pixel data in) must go to the same GPIO as **`PIN_DATA`** in `pico_ws2812_receiver.py` (default **GP12**).

3. **Logic level**  
   - Pico outputs **3.3 V**. Many WS2812 strips need **5 V logic** on DIN. Use a **level shifter** (for example 74AHCT125) between that GPIO and DIN if the strip is picky.

4. **NeoPixel timing**  
   - On the Pico, in `pico_ws2812_receiver.py`, set **`NEO_TIMING = 0`** instead of `1`, save as `main.py`, reset, and run `python scripts/ws2812_diag.py solid red` again.

5. **Bypass USB (pure hardware test)**  
   This lights only **LED 0** on the strip with both timing values (no Flask, no base64):

   ```bash
   mpremote connect /dev/cu.usbmodem101 run pico/hw_smoke_ws2812.py
   ```

   If **still nothing**, wiring or power is wrong, or DIN is not the input of the first pixel you think it is. If **LED 0 blinks** but the full panel test stays dark, suspect a very long strip, a bad first LED, or wrong `N` (256) for your actual layout (still, LED 0 should react).
