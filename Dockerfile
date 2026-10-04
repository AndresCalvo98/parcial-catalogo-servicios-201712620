FROM python:3.11-slim

# Metadata
LABEL maintainer="Andrés Calvo <201712620> — Software Avanzado USAC 2026"
LABEL description="Catálogo de Servicios TI — Backend FastAPI + PostgreSQL"

WORKDIR /app

# Environment settings
ENV PYTHONPATH=/app/src:/app:/app/scripts
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose port
EXPOSE 8000

# Entrypoint: production-ready (no --reload)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
