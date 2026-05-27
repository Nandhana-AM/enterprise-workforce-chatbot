# ─── Stage 1: Build Frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


# ─── Stage 2: Install Python Dependencies ─────────────────────────────────────
FROM python:3.11-slim AS python-builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm


# ─── Stage 3: Final Production Runtime ────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy built frontend assets to the location mounted by FastAPI static files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy backend application source
COPY backend/app ./backend/app

# Copy pre-generated synthetic dataset
COPY synthetic_skill_dataset.xlsx ./synthetic_skill_dataset.xlsx

# Create and use non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check using FastAPI health check route
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
