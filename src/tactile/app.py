"""Flask web application for Braille display and image pipeline."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from tactile.braille import translate_text
from tactile.image_pipeline import process_image_for_flask
from tactile.ws2812_matrix import (
    buffer_to_preview_grid,
    panel_mapping_from_env,
    panel_strip_index,
    render_braille_rgb_buffer,
)
from tactile.serial_board import clear_board, reset_board
from tactile.ws2812_serial_board import clear_ws2812_panel, send_ws2812_frame

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WS2812_TEXT_COLS = 11
WS2812_TEXT_ROWS = 2
# LED + detailed preview: one page = this many typed characters from the input string (11×2).
WS2812_CHARS_PER_PAGE = 22
WS2812_IMAGE_PANEL_WIDTH = 16
WS2812_IMAGE_PANEL_HEIGHT = 16

# Same as legacy flat layout: uploads live under the process cwd, not the package path.
UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

app = Flask(
    __name__,
    template_folder=str(_PROJECT_ROOT / "templates"),
    static_folder=str(_PROJECT_ROOT / "static"),
)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _preview_mapping(meta: dict) -> dict:
    return {
        "serpentine_rows": meta["serpentine_rows"],
        "flip_x": meta["flip_x"],
        "flip_y": meta["flip_y"],
        "column_major": meta["column_major"],
        "swap_axes": meta["swap_axes"],
    }


def _ws2812_character_page(text: str, page: int, chunk: int = WS2812_CHARS_PER_PAGE) -> dict:
    """Split plain text into fixed-size chunks so preview and LED stay within one physical page."""
    t = text or ""
    n = len(t)
    if n == 0:
        return {
            "page": 0,
            "total_pages": 1,
            "has_more": False,
            "page_text": "",
            "page_lines": [""],
        }
    total_pages = max(1, (n + chunk - 1) // chunk)
    page_idx = max(0, min(int(page or 0), total_pages - 1))
    start = page_idx * chunk
    end = min(start + chunk, n)
    fragment = t[start:end]
    has_more = end < n
    return {
        "page": page_idx,
        "total_pages": total_pages,
        "has_more": has_more,
        "page_text": fragment,
        "page_lines": fragment.splitlines() or ([fragment] if fragment else [""]),
    }


def _image_matrix_to_ws2812_rgb(
    flat_list: list[int],
    width: int,
    height: int,
    fg: tuple[int, int, int] = (255, 0, 0),
    bg: tuple[int, int, int] = (0, 0, 0),
) -> bytes:
    """
    Convert a logical 0/1 image matrix into a WS2812 RGB frame using
    flat_value list from process_image_for_flask
    """
    total_leds = width * height
    frame = bytearray(total_leds * 3)
    mapping = panel_mapping_from_env()
    try:
        brightness = float(os.environ.get("WS2812_BRIGHTNESS", "0.10"))
    except (TypeError, ValueError):
        brightness = 0.10
    brightness = max(0.0, min(1.0, brightness))
    lit_fg = tuple(min(255, max(0,int(round(c * brightness)))) for c in fg)

    for py in range(total_leds):
            value = flat_list[py]
            color = lit_fg if value else bg
            offset = value * 3
            frame[offset] = color[0]
            frame[offset + 1] = color[1]
            frame[offset + 2] = color[2]

    return bytes(frame)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/display", methods=["POST"])
def display():
    """
    Main "Display" action: Braille preview JSON plus WS2812 panel output (8x32).

    Optional JSON: fg [r,g,b], bg [r,g,b]. Strip serpentine: env WS2812_SERPENTINE
    (default on for 32×8 zig-zag panels).
    """
    data = request.get_json() or {}
    text = data.get("text", "")
    paginate = bool(data.get("paginate", True))
    if paginate and len(text) <= WS2812_CHARS_PER_PAGE:
        paginate = False
    if paginate:
        page_data = _ws2812_character_page(text, data.get("page", 0))
        page_text = page_data["page_text"]
        patterns = translate_text(page_text)
        patterns_rows = None
        page_lines = page_data["page_lines"]
    else:
        page_data = {
            "page": 0,
            "total_pages": 1,
            "has_more": False,
            "page_text": text,
            "page_lines": text.splitlines() if text else [""],
        }
        page_text = text
        patterns = translate_text(text)
        patterns_rows = None
        page_lines = page_data["page_lines"]
    fg = tuple(data.get("fg", [255, 0, 0]))
    bg = tuple(data.get("bg", [0, 0, 0]))
    rgb, meta = render_braille_rgb_buffer(page_text, fg=fg, bg=bg)
    preview = buffer_to_preview_grid(
        rgb, meta["width"], meta["height"], _preview_mapping(meta)
    )
    try:
        send_ws2812_frame(rgb)
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": str(e),
                    "patterns": patterns,
                    "meta": meta,
                    "preview": preview,
                    "page": page_data["page"],
                    "total_pages": page_data["total_pages"],
                    "has_more": page_data["has_more"],
                    "page_text": page_data["page_text"],
                    "page_lines": page_lines,
                    "patterns_rows": patterns_rows,
                    "max_chars_per_row": WS2812_TEXT_COLS,
                    "max_rows": WS2812_TEXT_ROWS,
                    "chars_per_page": WS2812_CHARS_PER_PAGE,
                }
            ),
            500,
        )
    return jsonify(
        {
            "status": "ok",
            "text": text,
            "patterns": patterns,
            "meta": meta,
            "preview": preview,
            "page": page_data["page"],
            "total_pages": page_data["total_pages"],
            "has_more": page_data["has_more"],
            "page_text": page_data["page_text"],
            "page_lines": page_lines,
            "patterns_rows": patterns_rows,
            "max_chars_per_row": WS2812_TEXT_COLS,
            "max_rows": WS2812_TEXT_ROWS,
            "chars_per_page": WS2812_CHARS_PER_PAGE,
        }
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def _handle_image_upload(send_to_led: bool):
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image file found."}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Unsupported file type."}), 400

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(save_path)

    try:
        result = process_image_for_flask(save_path)
        if send_to_led:
            panel_width = int(
                os.environ.get("WS2812_IMAGE_WIDTH", str(WS2812_IMAGE_PANEL_WIDTH))
            )
            panel_height = int(
                os.environ.get("WS2812_IMAGE_HEIGHT", str(WS2812_IMAGE_PANEL_HEIGHT))
            )
            image_width = int(result.get("target_width") or 0)
            image_height = int(result.get("target_height") or 0)
            if image_width > panel_width or image_height > panel_height:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": (
                                f"Image is {image_width}x{image_height}, but LED panel is "
                                f"{panel_width}x{panel_height}. Use a smaller image."
                            ),
                            "target_width": result.get("target_width"),
                            "target_height": result.get("target_height"),
                        }
                    ),
                    400,
                )
            rgb_frame = _image_matrix_to_ws2812_rgb(
                result.get("flat_values", []),
                panel_width,
                panel_height,
            )
            send_ws2812_frame(rgb_frame)

        image_url = url_for("uploaded_file", filename=unique_filename)

        return jsonify(
            {
                "status": "ok",
                "filename": unique_filename,
                "image_url": image_url,
                "rows": result.get("rows", []),
                "flat_values": result.get("flat_values", []),
                "pico_data": result.get("pico_data", ""),
                "target_width": result.get("target_width"),
                "target_height": result.get("target_height"),
                "threshold": result.get("threshold"),
                "braille_encoded_values": result.get("braille_encoded_values", []),
                "braille_flat_values": result.get("braille_flat_values", []),
                "braille_pico_data": result.get("braille_pico_data", ""),
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/upload_image", methods=["POST"])
@app.route("/image-display", methods=["POST"])
def upload_image():
    send_to_led = request.form.get("send_to_led", "1").lower() not in (
        "0",
        "false",
        "no",
    )
    return _handle_image_upload(send_to_led=send_to_led)


@app.route("/upload_image_simulation", methods=["POST"])
def upload_image_simulation():
    return _handle_image_upload(send_to_led=False)


@app.route("/reset", methods=["POST"])
def reset():
    reset_board()
    return jsonify({"status": "reset"})


@app.route("/clear", methods=["POST"])
def clear():
    clear_board()
    return jsonify({"status": "cleared"})


@app.route("/display_panel", methods=["POST"])
def display_panel():
    """
    Render Braille text on an 8x32 WS2812 grid (32 wide x 8 tall by default).
    JSON body: text (required), optional fg [r,g,b], bg [r,g,b].
    Serpentine strip order: env WS2812_SERPENTINE (default on).
    """
    data = request.get_json() or {}
    text = data.get("text", "")
    fg = tuple(data.get("fg", [255, 0, 0]))
    bg = tuple(data.get("bg", [0, 0, 0]))
    rgb, meta = render_braille_rgb_buffer(text, fg=fg, bg=bg)
    try:
        send_ws2812_frame(rgb)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "meta": meta}), 500
    preview = buffer_to_preview_grid(
        rgb, meta["width"], meta["height"], _preview_mapping(meta)
    )
    return jsonify({"status": "ok", "text": text, "meta": meta, "preview": preview})


@app.route("/clear_panel", methods=["POST"])
def clear_panel():
    try:
        clear_ws2812_panel()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    # use_reloader=False avoids two processes fighting over the USB serial port
    app.run(debug=True, use_reloader=False)
