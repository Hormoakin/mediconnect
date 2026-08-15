# ══════════════════════════════════════════════════════════════
# ENHANCEMENT 3: ENHANCED AI SYMPTOM CHECKER WITH TRIAGE
# ai_service/triage.py
#
# Extends the base SymptomChecker to add:
#   1. Department-level routing (maps specialist → department)
#   2. Available doctor lookup (queries Django backend)
#   3. Direct booking assist — returns a pre-filled booking payload
#   4. Urgency routing (emergency → A&E, high → specialist, low → GP)
# ══════════════════════════════════════════════════════════════
 
import logging
import aiohttp
import asyncio
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
 
from config import settings
from schemas import UrgencyLevel, PossibleCondition
from symptom_checker import SymptomChecker, DISCLAIMER
 
logger = logging.getLogger(__name__)
 
 
# ─────────────────────────────────────────────────────────────
# DEPARTMENT ROUTING MAP
# Maps specialist types to hospital departments and urgency rules
# ─────────────────────────────────────────────────────────────
DEPARTMENT_ROUTING = {
    # Emergency — go immediately, do not book
    'Emergency Medicine':   {'dept': 'Accident & Emergency (A&E)', 'priority': 1, 'emergency': True},
 
    # High priority — book specialist urgently
    'Cardiologist':         {'dept': 'Cardiology',                  'priority': 2, 'emergency': False},
    'Neurologist':          {'dept': 'Neurology',                   'priority': 2, 'emergency': False},
    'Haematologist':        {'dept': 'Haematology',                 'priority': 2, 'emergency': False},
    'Oncologist':           {'dept': 'Oncology',                    'priority': 2, 'emergency': False},
 
    # Standard specialist
    'Gynaecologist':        {'dept': 'Obstetrics & Gynaecology',    'priority': 3, 'emergency': False},
    'Obstetrician':         {'dept': 'Obstetrics & Gynaecology',    'priority': 3, 'emergency': False},
    'Paediatrician':        {'dept': 'Paediatrics',                 'priority': 3, 'emergency': False},
    'Orthopaedic Surgeon':  {'dept': 'Orthopaedics',                'priority': 3, 'emergency': False},
    'Pulmonologist':        {'dept': 'Respiratory Medicine',        'priority': 3, 'emergency': False},
    'Gastroenterologist':   {'dept': 'Gastroenterology',            'priority': 3, 'emergency': False},
    'Urologist':            {'dept': 'Urology',                     'priority': 3, 'emergency': False},
    'Endocrinologist':      {'dept': 'Endocrinology',               'priority': 3, 'emergency': False},
    'Nephrologist':         {'dept': 'Nephrology',                  'priority': 3, 'emergency': False},
    'Rheumatologist':       {'dept': 'Rheumatology',                'priority': 3, 'emergency': False},
    'Psychiatrist':         {'dept': 'Psychiatry',                  'priority': 3, 'emergency': False},
    'Dermatologist':        {'dept': 'Dermatology',                 'priority': 3, 'emergency': False},
    'Ophthalmologist':      {'dept': 'Ophthalmology',               'priority': 3, 'emergency': False},
    'ENT Specialist':       {'dept': 'Ear, Nose & Throat (ENT)',    'priority': 3, 'emergency': False},
 
    # Primary care — default
    'General Practitioner': {'dept': 'General Outpatient',          'priority': 4, 'emergency': False},
    'General Surgeon':      {'dept': 'General Surgery',             'priority': 3, 'emergency': False},
    'Dentist':              {'dept': 'Dental',                      'priority': 4, 'emergency': False},
}
 
 
# ─────────────────────────────────────────────────────────────
# TRIAGE SCHEMAS
# ─────────────────────────────────────────────────────────────
class TriageRecommendedDoctor(BaseModel):
    id:               int
    full_name:        str
    speciality:       str
    hospital_name:    str
    rating:           str
    consultation_fee: str
    is_available:     bool
    next_available_slot: Optional[str] = None
 
 
class TriageBookingPayload(BaseModel):
    """Pre-filled booking payload the frontend can use directly."""
    doctor_id:    int
    doctor_name:  str
    speciality:   str
    suggested_reason: str
 
 
class TriageResult(BaseModel):
    # Core symptom analysis
    symptoms_submitted:     str
    possible_conditions:    List[PossibleCondition]
    urgency_level:          UrgencyLevel
    urgency_reason:         str
    disclaimer:             str
 
    # Triage additions
    recommended_department: str
    department_priority:    int     # 1=emergency, 2=urgent, 3=standard, 4=routine
    is_emergency:           bool
    emergency_instruction:  Optional[str]
 
    # Available doctors
    available_doctors:      List[TriageRecommendedDoctor]
    total_doctors_found:    int
 
    # Booking assist
    booking_payload:        Optional[TriageBookingPayload]
    booking_instructions:   str
 
    # AI metadata
    response_time_ms:       int
    model_version:          str
 
 
# ─────────────────────────────────────────────────────────────
# ENHANCED TRIAGE SYMPTOM CHECKER
# ─────────────────────────────────────────────────────────────
class TriageSymptomChecker(SymptomChecker):
    """
    Extends SymptomChecker with department routing,
    available doctor lookup, and booking assist.
    """
 
    async def _fetch_available_doctors(
        self, specialist_type: str, token: Optional[str] = None
    ) -> List[dict]:
        """Fetch doctors from Django backend matching the specialist type."""
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
 
        try:
            async with aiohttp.ClientSession() as session:
                params = {'search': specialist_type, 'available': 'true', 'ordering': '-rating'}
                async with session.get(
                    f"{settings.backend_base_url}/api/v1/doctors/",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('results', data) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"Failed to fetch doctors for triage: {e}")
        return []
 
    async def _get_doctor_next_slot(
        self, doctor_id: int, token: Optional[str] = None
    ) -> Optional[str]:
        """Get the next available appointment slot for a doctor."""
        from datetime import date, timedelta
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
 
        for days_ahead in range(1, 8):  # Check next 7 days
            check_date = (date.today() + timedelta(days=days_ahead)).isoformat()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{settings.backend_base_url}/api/v1/doctors/{doctor_id}/slots/",
                        headers=headers,
                        params={'date': check_date},
                        timeout=aiohttp.ClientTimeout(total=3),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            slots = data.get('available_slots', [])
                            if slots:
                                return f"{check_date} {slots[0]}"
            except Exception:
                pass
        return None
 
    def _get_department_info(self, specialist_type: str) -> dict:
        """Lookup department routing for the recommended specialist."""
        # Direct match
        if specialist_type in DEPARTMENT_ROUTING:
            return DEPARTMENT_ROUTING[specialist_type]
 
        # Fuzzy match — find by keyword
        specialist_lower = specialist_type.lower()
        for spec, info in DEPARTMENT_ROUTING.items():
            if any(word in specialist_lower for word in spec.lower().split()):
                return info
 
        # Default to General Outpatient
        return {'dept': 'General Outpatient', 'priority': 4, 'emergency': False}
 
    def _urgency_to_booking_instruction(
        self, urgency: UrgencyLevel, is_emergency: bool, department: str
    ) -> str:
        if is_emergency or urgency == UrgencyLevel.EMERGENCY:
            return (
                "⚠️ EMERGENCY: Please go immediately to the nearest Accident & Emergency "
                "department or call emergency services. Do NOT wait for an appointment."
            )
        elif urgency == UrgencyLevel.HIGH:
            return (
                f"URGENT: Please book an appointment with the {department} department as soon as possible — "
                "ideally within the next 24–48 hours. If symptoms worsen, seek emergency care."
            )
        elif urgency == UrgencyLevel.MEDIUM:
            return (
                f"Please book an appointment with the {department} within the next few days. "
                "Monitor your symptoms — if they worsen significantly, seek urgent care."
            )
        else:
            return (
                f"Please book a routine appointment with the {department} at your convenience. "
                "Continue to monitor your symptoms."
            )
 
    async def triage(
        self,
        symptoms: str,
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        user_id: Optional[int] = None,
        auth_token: Optional[str] = None,
    ) -> TriageResult:
        """
        Full triage assessment:
          1. Analyse symptoms (ML + GPT-4o-mini)
          2. Map specialist → department
          3. Fetch available doctors in that specialty
          4. Build booking payload for the top-ranked doctor
        """
        import time
        start = time.time()
 
        # Step 1: Run base symptom analysis
        base_result = await self.analyse(
            symptoms=symptoms,
            patient_age=patient_age,
            patient_gender=patient_gender,
            user_id=user_id,
        )
 
        # Step 2: Department routing
        specialist     = base_result.analysis.recommended_specialist
        dept_info      = self._get_department_info(specialist)
        department     = dept_info['dept']
        is_emergency   = dept_info['emergency']
        priority       = dept_info['priority']
 
        # Override urgency level for emergency cases
        if is_emergency:
            urgency = UrgencyLevel.EMERGENCY
        else:
            urgency = base_result.analysis.urgency_level
 
        # Step 3: Fetch available doctors (skip for emergencies)
        available_doctors = []
        booking_payload   = None
 
        if not is_emergency:
            raw_doctors = await self._fetch_available_doctors(specialist, auth_token)
 
            # Get next slot for top 3 doctors in parallel
            slot_tasks = [
                self._get_doctor_next_slot(d.get('id', 0), auth_token)
                for d in raw_doctors[:3]
            ]
            slots = await asyncio.gather(*slot_tasks, return_exceptions=True)
 
            for i, doc in enumerate(raw_doctors[:5]):
                next_slot = slots[i] if i < len(slots) and not isinstance(slots[i], Exception) else None
                available_doctors.append(TriageRecommendedDoctor(
                    id=doc.get('id', 0),
                    full_name=doc.get('user_full_name', ''),
                    speciality=doc.get('speciality', specialist),
                    hospital_name=doc.get('hospital_name', ''),
                    rating=str(doc.get('rating', '0.0')),
                    consultation_fee=str(doc.get('consultation_fee', '0.00')),
                    is_available=doc.get('is_available', True),
                    next_available_slot=next_slot if not isinstance(next_slot, Exception) else None,
                ))
 
            # Step 4: Build booking payload for top doctor
            if available_doctors:
                top = available_doctors[0]
                condition_name = (
                    base_result.analysis.possible_conditions[0].condition
                    if base_result.analysis.possible_conditions else 'Consultation'
                )
                booking_payload = TriageBookingPayload(
                    doctor_id=top.id,
                    doctor_name=top.full_name,
                    speciality=top.speciality,
                    suggested_reason=(
                        f"AI-assisted triage referral: {condition_name} "
                        f"(urgency: {urgency.value}). Symptoms: {symptoms[:200]}"
                    ),
                )
 
        response_time_ms = int((time.time() - start) * 1000)
 
        return TriageResult(
            symptoms_submitted=symptoms,
            possible_conditions=base_result.analysis.possible_conditions,
            urgency_level=urgency,
            urgency_reason=base_result.analysis.urgency_reason,
            disclaimer=DISCLAIMER,
            recommended_department=department,
            department_priority=priority,
            is_emergency=is_emergency,
            emergency_instruction=(
                "Call emergency services immediately or go to the nearest A&E."
                if is_emergency else None
            ),
            available_doctors=available_doctors,
            total_doctors_found=len(available_doctors),
            booking_payload=booking_payload,
            booking_instructions=self._urgency_to_booking_instruction(urgency, is_emergency, department),
            response_time_ms=response_time_ms,
            model_version=base_result.model_version,
        )
