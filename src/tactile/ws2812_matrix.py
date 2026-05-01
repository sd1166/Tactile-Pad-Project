"""
Map Braille text to an 8x32 (height x width) WS2812 grid.

Layout (defaults, overridable via render_braille_rgb_buffer kwargs or env):
  - One LED per Braille dot: each cell is a 2 (wide) x 3 (tall) block. Only dots
    that are "on" in the pattern are lit; the other positions in the 2x3 stay
    at the background color.
  - Between each pair of Braille cells there is a full-height band of
    `col_gap` column(s) left at the background (no LEDs in that column are
    ever written, so they stay off at bg). Default: one off column.
  - Between each text line, `row_gap` full-width row(s) of background. Default: one.

Env (optional, integers): WS2812_COL_GAP, WS2812_ROW_GAP (defaults 1),
  WS2812_MARGIN_X, WS2812_MARGIN_Y (shift the whole Braille layout in pixels).
Env (optional, float 0..1): WS2812_BRIGHTNESS scales lit (foreground) RGB
(default 0.10). Set to 1.0 for full brightness.

Panel coordinates (Braille layout): origin top-left, x grows right, y grows down
(logical **32 wide x 8 tall**, matching Braille lines).

Defaults match a **32×8** panel wired like Adafruit ``NeoMatrix(32, 8, pin,
NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG, …)``: ``WS2812_SWAP_AXES=0`` (native 32×8
strip order), ``WS2812_COLUMN_MAJOR=1``, ``WS2812_SERPENTINE=1``. If your LEDs
count as **8×32** along the wire, set ``WS2812_SWAP_AXES=1`` so logical ``(x,y)``
maps to ``(y,x)`` on an 8×32 index grid.

``WS2812_FLIP_X`` and ``WS2812_FLIP_Y`` fix origin and mirroring after the swap
(Adafruit ``NEO_MATRIX_BOTTOM + NEO_MATRIX_RIGHT`` is not one line in our model;
tune flips until ``ws2812_diag.py compare`` and a test letter look right). Set
``WS2812_SERPENTINE=0`` for straight strip order if ``compare`` pattern A wins.

Pattern bits 0..5 map to cell positions:
  (0,0)(1,0)  -> dots 1,4
  (0,1)(1,1)  -> dots 2,5
  (0,2)(1,2)  -> dots 3,6
"""

import os

from tactile.braille import translate_text

DEFAULT_WIDTH = 32
DEFAULT_HEIGHT = 8
# Standard Braille cell: 2 columns x 3 rows of LEDs, one LED per dot position.
CELL_W = 2
CELL_H = 3
DEFAULT_COL_GAP = 1
DEFAULT_ROW_GAP = 1


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
    """Legacy row-major strip index (no flips). Prefer ``panel_strip_index``."""
    if x < 0 or x >= width or y < 0 or y >= height:
        return None
    if serpentine_rows and (y % 2 == 1):
        x = width - 1 - x
    return y * width + x


def _env_bool_default(name: str, default_when_unset: str) -> bool:
    return os.environ.get(name, default_when_unset).lower() in ("1", "true", "yes")


def panel_mapping_from_env(serpentine_rows: bool | None = None) -> dict:
    """
    Strip wiring options from env.

    WS2812_FLIP_X defaults off; WS2812_FLIP_Y defaults on (tune both for your corner).
    WS2812_COLUMN_MAJOR defaults on (column-first / ``NEO_MATRIX_COLUMNS``).
    WS2812_SWAP_AXES defaults off (native 32×8 like ``NeoMatrix(32, 8, …)``); set 1
    for 8×32 strip order.
    WS2812_SERPENTINE defaults on (``NEO_MATRIX_ZIGZAG``). Pass ``serpentine_rows``
    to override the env (used by diagnostics).
    """
    if serpentine_rows is None:
        sr = _env_bool_default("WS2812_SERPENTINE", "1")
    else:
        sr = bool(serpentine_rows)
    return {
        "serpentine_rows": sr,
        "flip_x": _env_bool_default("WS2812_FLIP_X", "1"),
        "flip_y": _env_bool_default("WS2812_FLIP_Y", "1"),
        "column_major": _env_bool_default("WS2812_COLUMN_MAJOR", "1"),
        "swap_axes": _env_bool_default("WS2812_SWAP_AXES", "0"),
    }


def _strip_index_rowcol(
    mx: int,
    my: int,
    mw: int,
    mh: int,
    serpentine_rows: bool,
    column_major: bool,
) -> int | None:
    """Linear index for ``mw`` x ``mh`` strip after bounds check (no flips)."""
    if mx < 0 or mx >= mw or my < 0 or my >= mh:
        return None
    if column_major:
        sy = my
        if serpentine_rows and (mx % 2 == 1):
            sy = mh - 1 - my
        return mx * mh + sy
    sx = mx
    if serpentine_rows and (my % 2 == 1):
        sx = mw - 1 - mx
    return my * mw + sx


def panel_strip_index(
    lx: int,
    ly: int,
    lw: int,
    lh: int,
    mapping: dict,
) -> int | None:
    """
    Map Braille logical pixel ``(lx, ly)`` in ``lw`` x ``lh`` (default 32x8) to
    linear WS2812 index 0..lw*lh-1.

    When ``swap_axes`` is true, the strip is treated as ``lh`` wide x ``lw`` tall
    (8x32): ``(lx, ly)`` becomes ``(ly, lx)`` before flips and row/column order.
    """
    if lx < 0 or lx >= lw or ly < 0 or ly >= lh:
        return None
    swap = mapping.get("swap_axes", False)
    if swap:
        mx, my = ly, lx
        mw, mh = lh, lw
    else:
        mx, my = lx, ly
        mw, mh = lw, lh
    if mapping["flip_x"]:
        mx = mw - 1 - mx
    if mapping["flip_y"]:
        my = mh - 1 - my
    return _strip_index_rowcol(
        mx,
        my,
        mw,
        mh,
        mapping.get("serpentine_rows", True),
        mapping["column_major"],
    )


def _parse_gap(name: str, default: int) -> int:
    try:
        return max(0, int(os.environ.get(name, str(default))))
    except (TypeError, ValueError):
        return default


def _parse_margin(name: str, default: int = 0) -> int:
    try:
        return max(0, int(os.environ.get(name, str(default))))
    except (TypeError, ValueError):
        return default


def _brightness() -> float:
    try:
        v = float(os.environ.get("WS2812_BRIGHTNESS", "0.10"))
    except (TypeError, ValueError):
        v = 0.10
    return max(0.0, min(1.0, v))


def render_braille_rgb_buffer(
    text,
    width=None,
    height=None,
    fg=(255, 0, 0),
    bg=(0, 0, 0),
    col_gap=None,
    row_gap=None,
):
    """
    Returns:
      rgb_bytes: length width*height*3 (RGB per LED)
      meta: dict with truncated, width, height, used_rect, col_gap, row_gap, …

    col_gap: columns of background only between each Braille cell (default
      DEFAULT_COL_GAP or env WS2812_COL_GAP). Each is a full column of off LEDs
      (background color) for all rows used by the cell.
    row_gap: background rows between lines (default DEFAULT_ROW_GAP or
      WS2812_ROW_GAP).
    Lit pixels use ``fg`` scaled by env ``WS2812_BRIGHTNESS`` (default 0.25).
    """
    text = text or ""
    width = width or int(os.environ.get("WS2812_WIDTH", str(DEFAULT_WIDTH)))
    height = height or int(os.environ.get("WS2812_HEIGHT", str(DEFAULT_HEIGHT)))
    if col_gap is None:
        col_gap = _parse_gap("WS2812_COL_GAP", DEFAULT_COL_GAP)
    else:
        col_gap = max(0, int(col_gap))
    if row_gap is None:
        row_gap = _parse_gap("WS2812_ROW_GAP", DEFAULT_ROW_GAP)
    else:
        row_gap = max(0, int(row_gap))
    char_pitch = CELL_W + col_gap
    line_pitch = CELL_H + row_gap
    margin_x = _parse_margin("WS2812_MARGIN_X", 0)
    margin_y = _parse_margin("WS2812_MARGIN_Y", 0)
    bright = _brightness()
    lit_fg = tuple(min(255, max(0, int(round(c * bright)))) for c in fg)
    panel_map = panel_mapping_from_env()

    n = width * height
    buf = bytearray(n * 3)
    for i in range(n):
        o = i * 3
        buf[o] = bg[0]
        buf[o + 1] = bg[1]
        buf[o + 2] = bg[2]

    def set_pixel(px, py, color):
        idx = panel_strip_index(px, py, width, height, panel_map)
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
            if not set_pixel(px, py, lit_fg):
                ok = False
        return ok

    max_y_used = -1
    max_x_used = -1
    truncated = False
    current_y = margin_y

    parts = text.splitlines()
    if not parts:
        parts = [""]
    for part in parts:
        x_cursor = margin_x
        y_row = current_y
        patterns = translate_text(part)
        for item in patterns:
            if x_cursor + CELL_W > width:
                y_row += line_pitch
                x_cursor = margin_x
            if y_row + CELL_H > height:
                truncated = True
                break

            pat = item.get("pattern", "000000")
            blit_cell(x_cursor, y_row, pat)
            max_y_used = max(max_y_used, y_row + CELL_H - 1)
            max_x_used = max(max_x_used, x_cursor + CELL_W - 1)
            x_cursor += char_pitch

        if truncated:
            break
        current_y = y_row + line_pitch
        if current_y >= height and part != parts[-1]:
            truncated = True
            break

    meta = {
        "width": width,
        "height": height,
        "truncated": truncated,
        "used_max_x": max_x_used,
        "used_max_y": max_y_used,
        "cell_w": CELL_W,
        "cell_h": CELL_H,
        "col_gap": col_gap,
        "row_gap": row_gap,
        "char_pitch": char_pitch,
        "line_pitch": line_pitch,
        "margin_x": margin_x,
        "margin_y": margin_y,
        "brightness": bright,
        "flip_x": panel_map["flip_x"],
        "flip_y": panel_map["flip_y"],
        "column_major": panel_map["column_major"],
        "serpentine_rows": panel_map["serpentine_rows"],
        "swap_axes": panel_map["swap_axes"],
    }
    return bytes(buf), meta


def buffer_to_preview_grid(rgb_bytes, width, height, mapping: dict | None = None):
    """
    0/1 grid in logical Braille coordinates (top-left origin) for JSON preview.
    Uses the same strip mapping as ``render_braille_rgb_buffer`` when ``mapping``
    is provided (pass ``meta`` subset from the render result).
    """
    rows = []
    for py in range(height):
        row = []
        for px in range(width):
            if mapping is not None:
                idx = panel_strip_index(px, py, width, height, mapping)
                if idx is None:
                    row.append(0)
                    continue
                o = idx * 3
            else:
                o = (py * width + px) * 3
            r, g, b = rgb_bytes[o], rgb_bytes[o + 1], rgb_bytes[o + 2]
            row.append(1 if (r or g or b) else 0)
        rows.append(row)
    return rows
