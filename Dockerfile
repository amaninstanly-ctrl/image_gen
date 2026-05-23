FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .
COPY start.sh .
RUN chmod +x start.sh

ENV PORT=8080
ENV OLLAMA_HOST=http://localhost:11434
ENV IMAGE_MODEL=x/z-image-turbo:fp8

EXPOSE 8080

CMD ["./start.sh"]
