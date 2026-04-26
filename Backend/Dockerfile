FROM python:3.11-slim

WORKDIR /app

# Install required build tools for packages like psutil, passlib, etc.
RUN apt-get update && apt-get install -y gcc g++ libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "pcg", "serve", "--host", "0.0.0.0", "--port", "8000"]
