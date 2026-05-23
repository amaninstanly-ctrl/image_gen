from flask import Flask, request, jsonify
import subprocess
import uuid
import os

app = Flask(__name__)

OUTPUT_DIR = "generated_images"

os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def home():
    return jsonify({
        "message": "Z-Image Turbo API Running"
    })


@app.route("/generate", methods=["POST"])
def generate_image():
    try:
        data = request.get_json()

        prompt = data.get("prompt")

        if not prompt:
            return jsonify({
                "error": "Prompt is required"
            }), 400

        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)

        command = [
            "ollama",
            "run",
            "x/z-image-turbo",
            prompt
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                "error": result.stderr
            }), 500

        return jsonify({
            "success": True,
            "message": "Image generated successfully",
            "output": result.stdout
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
