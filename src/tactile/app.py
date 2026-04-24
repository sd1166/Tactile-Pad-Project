"""Flask web application for Braille display and image pipeline."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from tactile.braille import translate_text
from tactile.image_pipeline import process_image_for_flask
from tactile.ws2812_matrix import buffer_to_preview_grid, render_braille_rgb_buffer
from tactile.serial_board import clear_board, reset_board
from tactile.ws2812_serial_board import clear_ws2812_panel, send_ws2812_frame

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

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
    patterns = translate_text(text)
    fg = tuple(data.get("fg", [255, 255, 255]))
    bg = tuple(data.get("bg", [0, 0, 0]))
    rgb, meta = render_braille_rgb_buffer(text, fg=fg, bg=bg)
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
        }
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/upload_image", methods=["POST"])
@app.route("/image-display", methods=["POST"])
def upload_image():
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
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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
    fg = tuple(data.get("fg", [255, 255, 255]))
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
