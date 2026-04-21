from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from braille import translate_text
import os

if os.environ.get("USE_FAKE_BOARD", "").lower() in ("1", "true", "yes"):
    from fake_board import send_to_board, reset_board, clear_board
else:
    from serial_board import send_to_board, reset_board, clear_board

from image_pipeline import process_image_for_flask
from werkzeug.utils import secure_filename
import uuid

from ws2812_matrix import render_braille_rgb_buffer, buffer_to_preview_grid
from ws2812_serial_board import send_ws2812_frame, clear_ws2812_panel

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/display", methods=["POST"])
def display():
    data = request.get_json()
    text = data.get("text", "")

    patterns = translate_text(text)
    send_to_board(patterns)

    return jsonify({
        "status": "ok",
        "text": text,
        "patterns": patterns
    })

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/upload_image", methods=["POST"])
@app.route("/image-display", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No image file found."
        }), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({
            "status": "error",
            "message": "No file selected."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": "Unsupported file type."
        }), 400

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(save_path)

    try:
        result = process_image_for_flask(save_path)

        image_url = url_for("uploaded_file", filename=unique_filename)

        return jsonify({
            "status": "ok",
            "filename": unique_filename,
            "image_url": image_url,
            "rows": result.get("rows", []),
            "flat_values": result.get("flat_values", []),
            "pico_data": result.get("pico_data", ""),
            "target_width": result.get("target_width"),
            "target_height": result.get("target_height"),
            "threshold": result.get("threshold")
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


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
    JSON body: text (required), optional fg [r,g,b], bg [r,g,b], serpentine bool.
    """
    data = request.get_json() or {}
    text = data.get("text", "")
    fg = tuple(data.get("fg", [255, 255, 255]))
    bg = tuple(data.get("bg", [0, 0, 0]))
    serpentine = bool(data.get("serpentine", False))
    rgb, meta = render_braille_rgb_buffer(
        text, fg=fg, bg=bg, serpentine_rows=serpentine
    )
    if os.environ.get("USE_FAKE_BOARD", "").lower() not in ("1", "true", "yes"):
        try:
            send_ws2812_frame(rgb)
        except OSError as e:
            return jsonify({"status": "error", "message": str(e), "meta": meta}), 500
    preview = buffer_to_preview_grid(rgb, meta["width"], meta["height"])
    return jsonify({
        "status": "ok",
        "text": text,
        "meta": meta,
        "preview": preview
    })


@app.route("/clear_panel", methods=["POST"])
def clear_panel():
    if os.environ.get("USE_FAKE_BOARD", "").lower() not in ("1", "true", "yes"):
        try:
            clear_ws2812_panel()
        except OSError as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    # use_reloader=False avoids two processes fighting over the USB serial port
    app.run(debug=True, use_reloader=False)