import os
import base64
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Ollama config — set OLLAMA_HOST in Railway environment variables
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemma3")  # change to your model name e.g. "llava", "bakllava"

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Image Generator</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #0a0a0f;
      --surface: #13131a;
      --border: #2a2a3a;
      --accent: #7c6aff;
      --accent2: #ff6a9e;
      --text: #e8e8f0;
      --muted: #6b6b80;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'DM Mono', monospace;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 48px 24px;
      background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(124,106,255,0.15), transparent),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,106,158,0.1), transparent);
    }

    header {
      text-align: center;
      margin-bottom: 48px;
    }

    header h1 {
      font-family: 'Syne', sans-serif;
      font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 800;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -1px;
    }

    header p {
      color: var(--muted);
      margin-top: 8px;
      font-size: 0.85rem;
      letter-spacing: 0.05em;
    }

    .card {
      width: 100%;
      max-width: 720px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 32px;
      box-shadow: 0 0 60px rgba(124,106,255,0.06);
    }

    label {
      display: block;
      font-size: 0.75rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 10px;
    }

    textarea {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      color: var(--text);
      font-family: 'DM Mono', monospace;
      font-size: 0.9rem;
      padding: 16px;
      resize: vertical;
      min-height: 110px;
      outline: none;
      transition: border-color 0.2s;
      line-height: 1.6;
    }

    textarea:focus {
      border-color: var(--accent);
    }

    textarea::placeholder { color: var(--muted); }

    .row {
      display: flex;
      gap: 16px;
      margin-top: 20px;
      flex-wrap: wrap;
    }

    .field {
      flex: 1;
      min-width: 140px;
    }

    select, input[type="number"] {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      color: var(--text);
      font-family: 'DM Mono', monospace;
      font-size: 0.85rem;
      padding: 10px 14px;
      outline: none;
      appearance: none;
      -webkit-appearance: none;
      transition: border-color 0.2s;
    }

    select:focus, input[type="number"]:focus {
      border-color: var(--accent);
    }

    button#generateBtn {
      margin-top: 24px;
      width: 100%;
      padding: 16px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      border: none;
      border-radius: 12px;
      color: #fff;
      font-family: 'Syne', sans-serif;
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.15s;
      position: relative;
      overflow: hidden;
    }

    button#generateBtn:hover { opacity: 0.9; transform: translateY(-1px); }
    button#generateBtn:active { transform: translateY(0); }
    button#generateBtn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

    #status {
      margin-top: 20px;
      font-size: 0.8rem;
      color: var(--muted);
      text-align: center;
      min-height: 20px;
      letter-spacing: 0.05em;
    }

    #status.error { color: #ff6a6a; }

    #output {
      margin-top: 32px;
      display: none;
    }

    #output h2 {
      font-family: 'Syne', sans-serif;
      font-size: 0.8rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 16px;
    }

    #output img {
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--border);
      display: block;
      animation: fadeIn 0.4s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .download-btn {
      display: inline-block;
      margin-top: 14px;
      padding: 10px 20px;
      background: transparent;
      border: 1px solid var(--accent);
      border-radius: 10px;
      color: var(--accent);
      font-family: 'DM Mono', monospace;
      font-size: 0.8rem;
      text-decoration: none;
      cursor: pointer;
      transition: background 0.2s, color 0.2s;
    }

    .download-btn:hover {
      background: var(--accent);
      color: #fff;
    }

    .spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
      margin-right: 8px;
    }

    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <header>
    <h1>Image Generator</h1>
    <p>powered by ollama &mdash; self-hosted</p>
  </header>

  <div class="card">
    <label for="prompt">Prompt</label>
    <textarea id="prompt" placeholder="A cinematic photo of a neon-lit Tokyo street at night, rain reflections, 8k..."></textarea>

    <div class="row">
      <div class="field">
        <label for="style">Style</label>
        <select id="style">
          <option value="">None</option>
          <option value="photorealistic, DSLR, 8k">Photorealistic</option>
          <option value="digital art, concept art, detailed">Digital Art</option>
          <option value="oil painting, fine art, textured">Oil Painting</option>
          <option value="anime style, vibrant colors">Anime</option>
          <option value="cinematic, film still, dramatic lighting">Cinematic</option>
          <option value="watercolor, soft edges, pastel">Watercolor</option>
        </select>
      </div>
      <div class="field">
        <label for="steps">Steps</label>
        <input type="number" id="steps" value="20" min="5" max="100"/>
      </div>
      <div class="field">
        <label for="seed">Seed (-1 = random)</label>
        <input type="number" id="seed" value="-1"/>
      </div>
    </div>

    <button id="generateBtn" onclick="generate()">Generate Image</button>
    <div id="status"></div>

    <div id="output">
      <h2>Result</h2>
      <img id="resultImg" src="" alt="Generated image"/>
      <br/>
      <a id="downloadBtn" class="download-btn" download="generated.png">↓ Download</a>
    </div>
  </div>

  <script>
    async function generate() {
      const prompt = document.getElementById('prompt').value.trim();
      if (!prompt) { setStatus('Please enter a prompt.', true); return; }

      const style = document.getElementById('style').value;
      const steps = parseInt(document.getElementById('steps').value) || 20;
      const seed  = parseInt(document.getElementById('seed').value);

      const fullPrompt = style ? `${prompt}, ${style}` : prompt;

      const btn = document.getElementById('generateBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>Generating...';
      document.getElementById('output').style.display = 'none';
      setStatus('Sending request to Ollama...');

      try {
        const res = await fetch('/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: fullPrompt, steps, seed })
        });

        const data = await res.json();

        if (data.error) { setStatus(data.error, true); return; }

        const imgSrc = `data:image/png;base64,${data.image}`;
        document.getElementById('resultImg').src = imgSrc;
        document.getElementById('downloadBtn').href = imgSrc;
        document.getElementById('output').style.display = 'block';
        setStatus('');
      } catch (e) {
        setStatus('Request failed: ' + e.message, true);
      } finally {
        btn.disabled = false;
        btn.innerHTML = 'Generate Image';
      }
    }

    function setStatus(msg, isError = false) {
      const el = document.getElementById('status');
      el.textContent = msg;
      el.className = isError ? 'error' : '';
    }

    document.getElementById('prompt').addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.ctrlKey) generate();
    });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    steps  = data.get("steps", 20)
    seed   = data.get("seed", -1)

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": steps,
        }
    }
    if seed != -1:
        payload["options"]["seed"] = seed

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=300
        )
        resp.raise_for_status()
        result = resp.json()

        # Ollama image models return base64 image in 'images' list
        images = result.get("images") or result.get("response_images")
        if images and len(images) > 0:
            return jsonify({"image": images[0]})

        # Some models embed image in response as base64 string directly
        response_text = result.get("response", "")
        if response_text and len(response_text) > 200:
            return jsonify({"image": response_text})

        return jsonify({"error": "No image returned from model. Check your IMAGE_MODEL env var."}), 500

    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Cannot connect to Ollama at {OLLAMA_HOST}. Check OLLAMA_HOST env var."}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Try fewer steps or a simpler prompt."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "ollama_host": OLLAMA_HOST, "model": IMAGE_MODEL})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
