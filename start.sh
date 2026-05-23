#!/bin/bash
set -e

echo ">>> Starting Ollama server..."
OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_NUM_PARALLEL=1 ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo ">>> Waiting for Ollama to be ready..."
for i in $(seq 1 60); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo ">>> Ollama is ready."
        break
    fi
    echo "    attempt $i/60..."
    sleep 3
done

# Pull model
MODEL="${IMAGE_MODEL:-x/z-image-turbo:fp8}"
echo ">>> Pulling model: $MODEL (this may take several minutes on first run...)"
ollama pull "$MODEL" && echo ">>> Model pull complete." || {
    echo "!!! Model pull failed. Trying fallback: jmorgan/z-image-turbo:fp8"
    ollama pull jmorgan/z-image-turbo:fp8 && export IMAGE_MODEL=jmorgan/z-image-turbo:fp8
}

echo ">>> Loaded models:"
ollama list

echo ">>> Starting Flask app on port ${PORT:-8080}..."
exec gunicorn app:app \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 1 \
    --timeout 600 \
    --keep-alive 5 \
    --log-level info
