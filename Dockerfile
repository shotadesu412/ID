# ----- Build stage -----
    FROM python:3.11-slim AS build
    WORKDIR /app
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
    COPY requirements.txt .
    RUN pip install --upgrade pip && pip install -r requirements.txt
    
    # ----- Runtime -----
    FROM python:3.11-slim
    WORKDIR /app
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        PORT=10000
    RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
    COPY --from=build /usr/local/lib/python3.11 /usr/local/lib/python3.11
    COPY --from=build /usr/local/bin /usr/local/bin
    COPY . .
    EXPOSE 10000
    CMD ["sh", "-c", "flask --app manage init-db && flask --app manage seed && gunicorn -w 2 --threads 2 -t 60 -b 0.0.0.0:10000 wsgi:app"]
    