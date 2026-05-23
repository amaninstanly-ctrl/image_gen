import os
import base64
import requests
from flask import Flask, request, jsonify, Response, send_file
import io

app = Flask(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "x/z-image-turbo:fp8")


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

    # Return raw response for debugging
    try:
        result = resp.json()
    except Exception:
        return None, f"Non-JSON response: {resp.text[:500]}"

    if resp.status_code != 200:
        return None, f"Ollama error {resp.status_code}: {result}"

    # z-image-turbo returns images in the 'images' field
    images = result.get("images") or result.get("response_images")
    if images and len(images) > 0:
        return images[0], None

    # Fallback: some models return base64 directly in 'response'
    response_text = result.get("response", "")
    if response_text and len(response_text) > 200:
        return response_text, None

    # Nothing found — return full result for debugging
    return None, f"No image in response. Keys: {list(result.keys())}. Response snippet: {str(result)[:300]}"


@app.route("/prompt")
def prompt_endpoint():
    q     = request.args.get("q", "").strip()
    steps = int(request.args.get("steps", 20))
    seed  = int(request.args.get("seed", -1))

    if not q:
        return Response(
            "Missing ?q= parameter.\nUsage: /prompt?q=a+red+fox",
            mimetype="text/plain", status=400
        )

    b64, err = call_ollama(q, steps=steps, seed=seed)

    if err:
        return Response(f"ERROR: {err}", mimetype="text/plain", status=500)

    img_bytes = base64.b64decode(b64)
    return send_file(io.BytesIO(img_bytes), mimetype="image/png", download_name="generated.png")


@app.route("/prompt", methods=["POST"])
def prompt_post():
    data  = request.get_json(silent=True) or {}
    q     = data.get("q", "").strip()
    steps = int(data.get("steps", 20))
    seed  = int(data.get("seed", -1))

    if not q:
        return jsonify({"error": "Missing 'q' field"}), 400

    b64, err = call_ollama(q, steps=steps, seed=seed)
    if err:
        return jsonify({"error": err}), 500

    return jsonify({"image": b64, "mime": "image/png"})


# Debug endpoint — shows Ollama status + loaded models
@app.route("/debug")
def debug():
    info = {"ollama_host": OLLAMA_HOST, "image_model": IMAGE_MODEL}
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        info["ollama_status"] = "reachable"
        info["models"] = r.json()
    except Exception as e:
        info["ollama_status"] = f"unreachable: {e}"

    # Try a tiny test generation to see raw error
    try:
        r2 = requests.post(f"{OLLAMA_HOST}/api/generate", json={
            "model": IMAGE_MODEL,
            "prompt": "test",
            "stream": False,
            "options": {"num_predict": 1}
        }, timeout=60)
        info["test_status"] = r2.status_code
        info["test_response"] = r2.json()
    except Exception as e:
        info["test_error"] = str(e)

    return jsonify(info)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "ollama_host": OLLAMA_HOST, "model": IMAGE_MODEL})


@app.route("/")
def index():
    host = request.host_url.rstrip("/")
    return Response(f"""IMAGE GENERATION API
====================

GET  {host}/prompt?q=your+prompt
GET  {host}/debug     ← check this if something is wrong
GET  {host}/health

Optional: &steps=20  &seed=42
""", mimetype="text/plain")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
