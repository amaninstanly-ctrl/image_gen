import os
import base64
import requests
from flask import Flask, request, jsonify, Response, send_file
import io

app = Flask(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemma3")


def call_ollama(prompt, steps=20, seed=-1):
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": steps},
    }
    if seed != -1:
        payload["options"]["seed"] = seed

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json=payload,
        timeout=300
    )
    resp.raise_for_status()
    result = resp.json()

    images = result.get("images") or result.get("response_images")
    if images and len(images) > 0:
        return images[0]

    response_text = result.get("response", "")
    if response_text and len(response_text) > 200:
        return response_text

    return None


# ─────────────────────────────────────────────
#  GET /prompt?q=a+red+fox&steps=20&seed=-1
#  Returns the raw PNG image directly —
#  paste the URL in <img src="...">, Notion,
#  Slack, anywhere.
# ─────────────────────────────────────────────
@app.route("/prompt")
def prompt_endpoint():
    q     = request.args.get("q", "").strip()
    steps = int(request.args.get("steps", 20))
    seed  = int(request.args.get("seed", -1))

    if not q:
        return Response(
            "Missing ?q= parameter.\n\n"
            "Usage: /prompt?q=a+red+fox+in+the+snow\n"
            "Optional: &steps=20  &seed=42",
            mimetype="text/plain",
            status=400
        )

    try:
        b64 = call_ollama(q, steps=steps, seed=seed)
    except requests.exceptions.ConnectionError:
        return Response(f"Cannot connect to Ollama at {OLLAMA_HOST}", mimetype="text/plain", status=502)
    except requests.exceptions.Timeout:
        return Response("Ollama timed out. Try fewer steps.", mimetype="text/plain", status=504)
    except Exception as e:
        return Response(str(e), mimetype="text/plain", status=500)

    if not b64:
        return Response("Model returned no image. Check IMAGE_MODEL env var.", mimetype="text/plain", status=500)

    img_bytes = base64.b64decode(b64)
    return send_file(
        io.BytesIO(img_bytes),
        mimetype="image/png",
        download_name="generated.png"
    )


# ─────────────────────────────────────────────
#  POST /prompt   { "q": "...", "steps": 20 }
#  Returns JSON { "image": "<base64>" }
#  for programmatic use / n8n / Make / etc.
# ─────────────────────────────────────────────
@app.route("/prompt", methods=["POST"])
def prompt_post():
    data  = request.get_json(silent=True) or {}
    q     = data.get("q", "").strip()
    steps = int(data.get("steps", 20))
    seed  = int(data.get("seed", -1))

    if not q:
        return jsonify({"error": "Missing 'q' field"}), 400

    try:
        b64 = call_ollama(q, steps=steps, seed=seed)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Cannot connect to Ollama at {OLLAMA_HOST}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Ollama timed out. Try fewer steps."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not b64:
        return jsonify({"error": "Model returned no image. Check IMAGE_MODEL env var."}), 500

    return jsonify({"image": b64, "mime": "image/png"})


# ─────────────────────────────────────────────
#  Health check
# ─────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "ollama_host": OLLAMA_HOST, "model": IMAGE_MODEL})


# ─────────────────────────────────────────────
#  Root — show usage docs
# ─────────────────────────────────────────────
@app.route("/")
def index():
    host = request.host_url.rstrip("/")
    return Response(f"""IMAGE GENERATION API
====================

GET  {host}/prompt?q=your+prompt
     → returns the PNG image directly
     → paste URL anywhere that accepts an image link

Optional params:
  &steps=20    number of diffusion steps (default 20)
  &seed=42     set seed for reproducibility (-1 = random)

POST {host}/prompt
     Body: {{ "q": "your prompt", "steps": 20, "seed": -1 }}
     → returns {{ "image": "<base64>", "mime": "image/png" }}

Examples:
  {host}/prompt?q=a+red+fox+in+the+snow
  {host}/prompt?q=futuristic+city+at+night&steps=30&seed=99

Health:
  {host}/health
""", mimetype="text/plain")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
