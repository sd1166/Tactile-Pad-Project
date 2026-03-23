from flask import Flask, render_template, request, jsonify
from braille import translate_text
from fake_board import send_to_board, reset_board, clear_board
from image_mapping.image_pipeline import process_image_for_flask
import os
from werkzeug.utils import secure_filename

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

@app.route("/upload_image", methods=["POST"])
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

    # Save the uploaded file safely
    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    try:
        # Call your image conversion function
        # This returns a dictionary with:
        # rows, flat_values, pico_data, target_width, target_height, threshold
        result = process_image_for_flask(save_path)

        return jsonify({
            "status": "ok",
            "filename": filename,
            "rows": result["rows"],
            "flat_values": result["flat_values"],
            "pico_data": result["pico_data"],
            "target_width": result["target_width"],
            "target_height": result["target_height"],
            "threshold": result["threshold"]
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