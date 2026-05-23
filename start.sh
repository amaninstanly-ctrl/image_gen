#!/bin/bash
set -e

echo ">>> Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo ">>> Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo ">>> Ollama is ready."
        break
    fi
    echo "    attempt $i/30..."
    sleep 2
done

# Pull model if not already present
MODEL="${IMAGE_MODEL:-x/z-image-turbo:fp8}"
echo ">>> Pulling model: $MODEL"
ollama pull "$MODEL"
echo ">>> Model ready."

# Start Flask app
echo ">>> Starting Flask app on port ${PORT:-8080}..."
exec gunicorn app:app \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 1 \
    --timeout 300 \
    --keep-alive 5 \
    --log-level info
