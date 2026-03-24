from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from braille import translate_text
from fake_board import send_to_board, reset_board, clear_board
from image_mapping.image_pipeline import process_image_for_flask
import os
from werkzeug.utils import secure_filename
import uuid

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

# Added: route for serving uploaded images back to frontend
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Added: support both old and new frontend route names
@app.route("/upload_image", methods=["POST"])
@app.route("/image-display", methods=["POST"])
def upload_image():
    # Check if the request contains an image file field named "image"
    if "image" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No image file found in request."
        }), 400

    file = request.files["image"]

    # Check if the user selected a file
    if file.filename == "":
        return jsonify({
            "status": "error",
            "message": "No file selected."
        }), 400

    # Check if the file extension is supported
    if not allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": "Unsupported file type."
        }), 400

    # Save the uploaded file safely with a unique filename
    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(save_path)

    try:
        # Call image conversion function
        result = process_image_for_flask(save_path)

        # Build an accessible URL for frontend preview
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

if __name__ == "__main__":
    app.run(debug=True)