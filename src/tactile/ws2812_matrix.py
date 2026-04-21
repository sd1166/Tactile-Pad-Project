"""
Map Braille text to an 8x32 (height x width) WS2812 grid.

Layout (defaults, overridable via kwargs or env in caller):
  - Each Braille cell uses a 2x3 block of LEDs (one LED per dot).
  - One blank column between characters (after the 2-dot-wide cell).
  - One blank row between lines (after the 3-dot-tall cell row).

Panel coordinates: origin top-left, x grows right, y grows down.
Flat index default: row-major idx = y * width + x.

Pattern bits 0..5 map to cell positions:
  (0,0)(1,0)  -> dots 1,4
  (0,1)(1,1)  -> dots 2,5
  (0,2)(1,2)  -> dots 3,6
"""

import os

from tactile.braille import translate_text

DEFAULT_WIDTH = 32
DEFAULT_HEIGHT = 8
CELL_W = 2
CELL_H = 3
COL_GAP = 1
ROW_GAP = 1
LINE_PITCH = CELL_H + ROW_GAP
CHAR_PITCH = CELL_W + COL_GAP


def pattern_bit_to_xy_in_cell(bit_index):
    """bit_index 0..5 -> (dx, dy) within 2x3 cell."""
    if bit_index == 0:
        return (0, 0)
    if bit_index == 1:
        return (0, 1)
    if bit_index == 2:
        return (0, 2)
    if bit_index == 3:
        return (1, 0)
    if bit_index == 4:
        return (1, 1)
    if bit_index == 5:
        return (1, 2)
    return (0, 0)


def flat_index(x, y, width, height, serpentine_rows=False):
    if x < 0 or x >= width or y < 0 or y >= height:
        return None
    if serpentine_rows and (y % 2 == 1):
        x = width - 1 - x
    return y * width + x


def render_braille_rgb_buffer(
    text,
    width=None,
    height=None,
    fg=(255, 255, 255),
    bg=(0, 0, 0),
    serpentine_rows=False,
):
    """
    Returns:
      rgb_bytes: length width*height*3 (RGB per LED)
      meta: dict with truncated, width, height, used_rect
    """
    text = text or ""
    width = width or int(os.environ.get("WS2812_WIDTH", str(DEFAULT_WIDTH)))
    height = height or int(os.environ.get("WS2812_HEIGHT", str(DEFAULT_HEIGHT)))

    n = width * height
    buf = bytearray(n * 3)
    for i in range(n):
        o = i * 3
        buf[o] = bg[0]
        buf[o + 1] = bg[1]
        buf[o + 2] = bg[2]

    def set_pixel(px, py, color):
        idx = flat_index(px, py, width, height, serpentine_rows)
        if idx is None:
            return False
        o = idx * 3
        buf[o] = color[0]
        buf[o + 1] = color[1]
        buf[o + 2] = color[2]
        return True

    def blit_cell(x0, y0, pattern):
        p = ((pattern or "") + "000000")[:6]
        ok = True
        for bi in range(6):
            if p[bi] != "1":
                continue
            dx, dy = pattern_bit_to_xy_in_cell(bi)
            px, py = x0 + dx, y0 + dy
            if px >= width or py >= height:
                ok = False
                continue
            if not set_pixel(px, py, fg):
                ok = False
        return ok

    max_y_used = -1
    max_x_used = -1
    truncated = False
    current_y = 0

    parts = text.splitlines()
    if not parts:
        parts = [""]
    for part in parts:
        x_cursor = 0
        y_row = current_y
        patterns = translate_text(part)
        for item in patterns:
            if x_cursor + CELL_W > width:
                y_row += LINE_PITCH
                x_cursor = 0
            if y_row + CELL_H > height:
                truncated = True
                break

            pat = item.get("pattern", "000000")
            blit_cell(x_cursor, y_row, pat)
            max_y_used = max(max_y_used, y_row + CELL_H - 1)
            max_x_used = max(max_x_used, x_cursor + CELL_W - 1)
            x_cursor += CHAR_PITCH

        if truncated:
            break
        current_y = y_row + LINE_PITCH
        if current_y >= height and part != parts[-1]:
            truncated = True
            break

    meta = {
        "width": width,
        "height": height,
        "truncated": truncated,
        "used_max_x": max_x_used,
        "used_max_y": max_y_used,
        "char_pitch": CHAR_PITCH,
        "line_pitch": LINE_PITCH,
    }
    return bytes(buf), meta


def buffer_to_preview_grid(rgb_bytes, width, height):
    """0/1 grid for JSON preview (foreground detection: any channel > 0)."""
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            i = (y * width + x) * 3
            r, g, b = rgb_bytes[i], rgb_bytes[i + 1], rgb_bytes[i + 2]
            row.append(1 if (r or g or b) else 0)
        rows.append(row)
    return rows
