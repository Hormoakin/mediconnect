# ══════════════════════════════════════════════════════════════
# ai_service/recommender.py
#
# Doctor Recommendation Engine (Chapter 3, Section 3.8.2).
# Five-factor weighted scoring algorithm:
#   40% — Speciality match (symptom-specialisation cosine similarity)
#   25% — Doctor availability (has active schedule slots this week)
#   20% — Rating (1–5 stars, weighted average from verified reviews)
#   10% — Location proximity (placeholder: same hospital area)
#    5% — Consultation fee alignment (lower fee = slightly higher score)
# ══════════════════════════════════════════════════════════════
import logging
import aiohttp
from typing import Optional, List
from config import settings
from schemas import DoctorRecommendResponse, RecommendedDoctor

logger = logging.getLogger(__name__)


class DoctorRecommender:
    """
    Fetches the doctor list from the Django backend via an internal
    service call and applies the multi-factor scoring algorithm.
    Separating this into the AI service (rather than the Django view)
    allows the scoring logic to be independently tested and updated
    without redeploying the main API.
    """

    # ── Scoring weights (must sum to 1.0) ─────────────────────
    WEIGHTS = {
        "speciality_match": 0.40,
        "availability":     0.25,
        "rating":           0.20,
        "location":         0.10,
        "fee_alignment":    0.05,
    }

    # ── Speciality keyword mappings ───────────────────────────
    SPECIALITY_KEYWORDS = {
        "general practitioner": ["general", "gp", "primary", "family", "medicine"],
        "cardiologist":         ["heart", "cardiac", "cardiovascular", "chest"],
        "neurologist":          ["brain", "neuro", "headache", "seizure", "stroke", "spine"],
        "paediatrician":        ["child", "paed", "pediatric", "infant", "baby"],
        "gynaecologist":        ["gyn", "women", "obstet", "pregnancy", "uterus"],
        "dermatologist":        ["skin", "derm", "rash", "acne"],
        "orthopaedic surgeon":  ["bone", "joint", "ortho", "fracture", "knee", "hip"],
        "psychiatrist":         ["mental", "psych", "depression", "anxiety", "emotion"],
        "endocrinologist":      ["diabetes", "thyroid", "hormone", "endo"],
        "pulmonologist":        ["lung", "pulmo", "breath", "respiratory", "asthma"],
        "gastroenterologist":   ["gastro", "stomach", "intestine", "bowel", "liver"],
        "urologist":            ["urology", "kidney", "bladder", "prostate"],
        "haematologist":        ["blood", "haem", "anaemia", "sickle"],
        "ophthalmologist":      ["eye", "ophthal", "vision", "sight"],
        "ent specialist":       ["ear", "nose", "throat", "ent"],
        "oncologist":           ["cancer", "tumor", "oncol", "lymph"],
        "rheumatologist":       ["joint", "rheuma", "arthritis", "autoimmune"],
        "nephrologist":         ["kidney", "renal", "nephro"],
        "emergency medicine":   ["emergency", "trauma", "accident", "critical"],
    }

    def __init__(self):
        self._backend_url = settings.backend_base_url
        logger.info("✅ DoctorRecommender initialised")

    # ── Fetch doctors from Django backend ─────────────────────
    async def _fetch_doctors(self, token: Optional[str] = None) -> List[dict]:
        """
        Calls the internal Django /api/v1/doctors/ endpoint.
        In production, the AI service authenticates with the backend
        using a shared internal service token (same mechanism as the
        WebSocket service → backend notification in Phase 3).
        """
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._backend_url}/api/v1/doctors/",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("results", data) if isinstance(data, dict) else data
                    logger.warning(f"Backend returned {resp.status} for /api/v1/doctors/")
                    return []
        except Exception as e:
            logger.error(f"Failed to fetch doctors from backend: {e}")
            return []

    # ── Scoring functions ─────────────────────────────────────
    def _speciality_score(self, doctor_speciality: str, requested_type: str) -> float:
        """Returns 0.0–1.0 based on how well speciality matches the request."""
        doc_spec = doctor_speciality.lower()
        req_type = requested_type.lower()

        # Exact match
        if req_type in doc_spec or doc_spec in req_type:
            return 1.0

        # Keyword match from synonym map
        for canonical, keywords in self.SPECIALITY_KEYWORDS.items():
            if any(kw in req_type for kw in keywords):
                if any(kw in doc_spec for kw in keywords):
                    return 0.75

        # Partial word overlap
        req_words = set(req_type.split())
        doc_words = set(doc_spec.split())
        overlap   = req_words & doc_words
        if overlap:
            return 0.4

        return 0.0

    def _availability_score(self, doctor: dict) -> float:
        """1.0 if doctor has active availability slots, 0.0 otherwise."""
        if not doctor.get("is_available", False):
            return 0.0
        availability = doctor.get("availability", [])
        active = [a for a in availability if a.get("is_active", True)]
        return 1.0 if active else 0.5

    def _rating_score(self, doctor: dict) -> float:
        """Normalises rating from 0–5 scale to 0.0–1.0."""
        try:
            rating = float(doctor.get("rating", 0))
            return min(rating / 5.0, 1.0)
        except (ValueError, TypeError):
            return 0.0

    def _fee_score(self, doctor: dict, max_fee: Optional[float]) -> float:
        """Lower fee relative to max = higher score. Range 0.0–1.0."""
        try:
            fee = float(doctor.get("consultation_fee", 0))
        except (ValueError, TypeError):
            return 0.5

        if max_fee is None or max_fee <= 0:
            # No fee preference — score inversely on absolute value
            # (₦0–₦5,000 → 1.0, ₦50,000+ → 0.0)
            return max(0.0, 1.0 - fee / 50000)

        if fee > max_fee:
            return 0.0
        return 1.0 - (fee / max_fee) * 0.5   # Even free doctors get max 1.0

    # ── Main recommendation entry point ───────────────────────
    async def recommend(
        self,
        specialist_type: str,
        symptoms: Optional[str] = None,
        max_fee: Optional[float] = None,
        available_only: bool = True,
        token: Optional[str] = None,
    ) -> DoctorRecommendResponse:

        doctors = await self._fetch_doctors(token)

        if not doctors:
            return DoctorRecommendResponse(
                specialist_type=specialist_type,
                recommendations=[],
                total_found=0,
                scoring_factors=self.WEIGHTS,
            )

        # Filter unavailable doctors if requested
        if available_only:
            doctors = [d for d in doctors if d.get("is_available", True)]

        scored: List[tuple[float, dict]] = []

        for doc in doctors:
            speciality = doc.get("speciality", "")

            s_spec  = self._speciality_score(speciality, specialist_type)
            s_avail = self._availability_score(doc)
            s_rat   = self._rating_score(doc)
            s_fee   = self._fee_score(doc, max_fee)

            # Location score: placeholder 0.5 until geolocation is added
            s_loc = 0.5

            total_score = (
                s_spec  * self.WEIGHTS["speciality_match"] +
                s_avail * self.WEIGHTS["availability"]     +
                s_rat   * self.WEIGHTS["rating"]           +
                s_loc   * self.WEIGHTS["location"]         +
                s_fee   * self.WEIGHTS["fee_alignment"]
            )

            scored.append((total_score, doc))

        # Sort descending by score, top 3
        scored.sort(key=lambda x: x[0], reverse=True)
        top_3 = scored[:3]

        recommendations = []
        for score, doc in top_3:
            recommendations.append(RecommendedDoctor(
                id=doc.get("id", 0),
                user_full_name=doc.get("user_full_name", ""),
                speciality=doc.get("speciality", ""),
                rating=str(doc.get("rating", "0.0")),
                years_experience=doc.get("years_experience", 0),
                consultation_fee=str(doc.get("consultation_fee", "0.00")),
                hospital_name=doc.get("hospital_name", ""),
                is_available=doc.get("is_available", True),
                score=round(score, 4),
            ))

        return DoctorRecommendResponse(
            specialist_type=specialist_type,
            recommendations=recommendations,
            total_found=len(scored),
            scoring_factors=self.WEIGHTS,
        )
