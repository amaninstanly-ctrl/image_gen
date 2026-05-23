FROM ollama/ollama

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-pip

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ollama serve & sleep 10 && ollama pull x/z-image-turbo && gunicorn -b 0.0.0.0:8080 app:app
