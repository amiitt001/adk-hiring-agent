FROM python:3.11-slim

WORKDIR /app

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh run.sh

ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080

CMD ["./start.sh"]
