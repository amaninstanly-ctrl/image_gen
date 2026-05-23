FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Railway injects PORT at runtime — gunicorn reads it via shell
ENV PORT=8080

EXPOSE 8080

# Use gunicorn for production on Railway
CMD gunicorn app:app \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --timeout 300 \
    --keep-alive 5 \
    --log-level info
