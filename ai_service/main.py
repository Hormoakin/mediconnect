# ══════════════════════════════════════════════════════════════
# ai_service/main.py
# MediConnect AI Microservice — FastAPI application entry point.
#
# Design rationale (Chapter 3, Section 3.4.1):
#  Isolated as a separate service from the Django backend because
#  GPT-4 API calls (1–3s) would exhaust Gunicorn workers and
#  violate NFR-01 (500ms p95) if run in-process with CRUD routes.
# ══════════════════════════════════════════════════════════════
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import time

from config import settings
from schemas import (
    SymptomCheckRequest, SymptomCheckResponse,
    DoctorRecommendRequest, DoctorRecommendResponse,
    HealthResponse,
)
from symptom_checker import SymptomChecker
from recommender import DoctorRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Global service instances (loaded once at startup) ─────────
symptom_checker: SymptomChecker = None
recommender: DoctorRecommender  = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models at startup, release at shutdown."""
    global symptom_checker, recommender
    logger.info("Loading MediConnect AI models...")
    symptom_checker = SymptomChecker()
    recommender     = DoctorRecommender()
    logger.info("✅ AI models loaded — service ready")
    yield
    logger.info("Shutting down AI service...")


app = FastAPI(
    title="MediConnect AI Service",
    description="AI-powered symptom checking and doctor recommendation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ── Request timing middleware ──────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time-Ms"] = str(int((time.time() - start) * 1000))
    return response


# ── Exception handler ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={"error": True, "message": "AI service temporarily unavailable. Please try again."}
    )


# ── Health check ──────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "mediconnect-ai",
        "version": "1.0.0",
        "models_loaded": symptom_checker is not None and recommender is not None,
    }


# ── Symptom Checker ───────────────────────────────────────────
@app.post(
    "/api/v1/ai/symptom-check",
    response_model=SymptomCheckResponse,
    tags=["AI"],
    summary="Analyse patient-reported symptoms (FR-04.1, FR-04.2)",
)
async def check_symptoms(request: SymptomCheckRequest):
    if symptom_checker is None:
        raise HTTPException(status_code=503, detail="AI service not ready")

    if len(request.symptoms.strip()) < 5:
        raise HTTPException(status_code=422, detail="Please describe your symptoms in more detail.")

    result = await symptom_checker.analyse(
        symptoms=request.symptoms,
        patient_age=request.patient_age,
        patient_gender=request.patient_gender,
    )
    return result


# ── Doctor Recommendation ─────────────────────────────────────
@app.post(
    "/api/v1/ai/recommend-doctor",
    response_model=DoctorRecommendResponse,
    tags=["AI"],
    summary="Recommend doctors based on symptoms and specialist type (FR-04.3)",
)
async def recommend_doctor(request: DoctorRecommendRequest):
    if recommender is None:
        raise HTTPException(status_code=503, detail="AI service not ready")

    result = await recommender.recommend(
        specialist_type=request.specialist_type,
        symptoms=request.symptoms,
        max_fee=request.max_fee,
        available_only=request.available_only,
    )
    return result


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
        workers=2,
    )
