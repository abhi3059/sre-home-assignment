# ──────────────── Stage 1: Builder ────────────────
FROM python:3.11-slim AS builder

# Set environment variables to avoid interactive installs and ensure reliability
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build tools
RUN apt-get update && apt-get install -y build-essential

# Create working directory
WORKDIR /app

# Install dependencies separately for layer caching
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --user -r requirements.txt

# ──────────────── Stage 2: Final ────────────────
FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Install runtime dependencies only
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY app/ ./app/
COPY app/main.py ./main.py

# Expose port
EXPOSE 8000

# Start FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
