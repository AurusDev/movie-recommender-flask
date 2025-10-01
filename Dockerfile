FROM python:3.11-slim

# Set envs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    GUNICORN_WORKERS=3 \
    GUNICORN_THREADS=4 \
    GUNICORN_TIMEOUT=120

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install deps first (better caching)
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY . /app

# Healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://127.0.0.1:${PORT}/ || exit 1

# Expose port
EXPOSE ${PORT}

# Run
CMD exec gunicorn -w ${GUNICORN_WORKERS} -k gthread --threads ${GUNICORN_THREADS} \
    --timeout ${GUNICORN_TIMEOUT} -b 0.0.0.0:${PORT} app:app

