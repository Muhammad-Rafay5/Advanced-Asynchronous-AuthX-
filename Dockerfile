# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final runtime
FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Install packages
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/*

# Non-root user setup
RUN adduser --disabled-password appuser

# Copy application files and set ownership
COPY --chown=appuser:appuser . .

# Ensure entrypoint is executable
RUN chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

# Entrypoint script runs migrations and starts gunicorn
ENTRYPOINT ["./entrypoint.sh"]
