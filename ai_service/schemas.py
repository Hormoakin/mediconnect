# ══════════════════════════════════════════════════════════════
# ai_service/schemas.py
# Pydantic request/response schemas for all AI endpoints.
# ══════════════════════════════════════════════════════════════
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum
 
 
class UrgencyLevel(str, Enum):
    LOW       = "low"
    MEDIUM    = "medium"
    HIGH      = "high"
    EMERGENCY = "emergency"
 
 
# ── Symptom Checker ───────────────────────────────────────────
class SymptomCheckRequest(BaseModel):
    symptoms:       str = Field(..., min_length=5, max_length=2000,
                                description="Patient's free-text symptom description")
    patient_age:    Optional[int] = Field(None, ge=0, le=120)
    patient_gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
 
    @field_validator("symptoms")
    @classmethod
    def strip_symptoms(cls, v: str) -> str:
        return v.strip()
 
 
class PossibleCondition(BaseModel):
    condition:   str
    confidence:  float = Field(..., ge=0.0, le=1.0)
    description: str
 
 
class SymptomAnalysis(BaseModel):
    possible_conditions:    List[PossibleCondition]
    urgency_level:          UrgencyLevel
    urgency_reason:         str
    recommended_specialist: str
    recommended_actions:    List[str]
    red_flags:              List[str]
    disclaimer:             str
 
    # FR-04.4: disclaimer is ALWAYS present — enforced here at schema level
    @field_validator("disclaimer")
    @classmethod
    def disclaimer_must_be_set(cls, v: str) -> str:
        if not v or len(v) < 20:
            raise ValueError("disclaimer must always be present")
        return v
 
 
class SymptomCheckResponse(BaseModel):
    symptoms_submitted: str
    analysis:           SymptomAnalysis
    response_time_ms:   int
    model_version:      str
 
 
# ── Doctor Recommendation ─────────────────────────────────────
class DoctorRecommendRequest(BaseModel):
    specialist_type: str = Field(..., min_length=3, max_length=100)
    symptoms:        Optional[str] = Field(None, max_length=2000)
    max_fee:         Optional[float] = Field(None, ge=0)
    available_only:  bool = True
 
 
class RecommendedDoctor(BaseModel):
    id:               int
    user_full_name:   str
    speciality:       str
    rating:           str
    years_experience: int
    consultation_fee: str
    hospital_name:    str
    is_available:     bool
    score:            float
 
 
class DoctorRecommendResponse(BaseModel):
    specialist_type: str
    recommendations: List[RecommendedDoctor]
    total_found:     int
    scoring_factors: dict
 
 
# ── Health check ──────────────────────────────────────────────
class HealthResponse(BaseModel):
    status:        str
    service:       str
    version:       str
    models_loaded: bool
 
