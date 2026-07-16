# ══════════════════════════════════════════════════════════════
# ai_service/Dockerfile
# ══════════════════════════════════════════════════════════════
# Multi-stage build:
#   builder  — installs deps + trains/downloads ML model
#   runtime  — minimal image with pre-built artefacts
#
# Build: docker buildx build --platform linux/amd64 \
#           -t hormoakin001/mediconnect-ai:latest --push ./ai_service
# ══════════════════════════════════════════════════════════════
 
# ── builder stage ─────────────────────────────────────────────
# FROM python:3.11-slim AS builder
# WORKDIR /build
# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt
# COPY . .
# # Pre-train the ML model so the container starts faster
# RUN python -c "
# from symptom_checker import SymptomChecker
# import os; os.environ.setdefault('OPENAI_API_KEY','placeholder')
# sc = SymptomChecker()
# print('Model trained and saved to /build/models/')
# "
 
# ── runtime stage ─────────────────────────────────────────────
# FROM python:3.11-slim AS runtime
# WORKDIR /app
#
# # Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc libpq-dev curl && \
#     rm -rf /var/lib/apt/lists/*
#
# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt
#
# # Copy application code
# COPY --from=builder /build .
# # Copy pre-trained model artefacts
# COPY --from=builder /build/models ./models
#
# # Non-root user for security
# RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
# RUN chown -R appuser:appgroup /app
# USER appuser
#
# EXPOSE 8001
#
# HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
#   CMD curl -f http://localhost:8001/health || exit 1
#
# CMD ["uvicorn", "main:app", \
#      "--host", "0.0.0.0", \
#      "--port", "8001", \
#      "--workers", "2", \
#      "--log-level", "info"]
 
