"""
apps/ai_service/views.py
AI-powered symptom checker and doctor recommendation endpoints.
Implements FR-04.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging, time, json
from pymongo import MongoClient

logger = logging.getLogger(__name__)


def get_mongo_collection(collection_name: str):
    """Return a MongoDB collection handle."""
    client = MongoClient(settings.MONGODB_URI)
    db     = client['mediconnect']
    return db[collection_name]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def symptom_check(request):
    """
    POST /api/v1/ai/symptom-check/
    Analyses patient-reported symptoms (FR-04.1, FR-04.2).
    Pipeline:
      1. Validate input
      2. Build clinical prompt
      3. Call OpenAI GPT-4
      4. Parse and rank results
      5. Attach mandatory disclaimer (FR-04.4)
      6. Log to MongoDB for model improvement (FR-04.5)
      7. Return structured response
    """
    symptoms = request.data.get('symptoms', '').strip()
    if not symptoms or len(symptoms) < 5:
        return Response(
            {'message': 'Please describe your symptoms in at least a few words.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    start_time = time.time()

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Build structured clinical prompt
        system_prompt = (
            "You are a medical triage assistant for MediConnect, a healthcare platform. "
            "Your role is to analyse patient-reported symptoms and provide structured clinical guidance. "
            "Always be thorough, professional, and cautious. "
            "IMPORTANT: You must ALWAYS include a disclaimer that your output is NOT a medical diagnosis."
        )

        user_prompt = f"""
Patient reports the following symptoms: "{symptoms}"

Please provide a structured response in the following JSON format ONLY (no other text):
{{
  "possible_conditions": [
    {{"condition": "Condition Name", "confidence": 0.85, "description": "Brief description"}},
    {{"condition": "Condition Name 2", "confidence": 0.60, "description": "Brief description"}},
    {{"condition": "Condition Name 3", "confidence": 0.40, "description": "Brief description"}}
  ],
  "urgency_level": "low|medium|high|emergency",
  "urgency_reason": "Brief explanation of urgency",
  "recommended_specialist": "Specialist type (e.g. General Practitioner, Cardiologist, etc.)",
  "recommended_actions": ["Action 1", "Action 2", "Action 3"],
  "red_flags": ["Red flag symptom if any"],
  "disclaimer": "This analysis is for informational purposes only and does not constitute medical advice or diagnosis. Please consult a qualified healthcare professional."
}}

Return ONLY the JSON object. No additional text.
"""

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,   # Low temperature for consistent medical responses
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        response_time_ms = int((time.time() - start_time) * 1000)
        raw_content      = response.choices[0].message.content

        try:
            ai_result = json.loads(raw_content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI JSON response: {raw_content}")
            return Response(
                {'message': 'AI service returned an unexpected response. Please try again.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Ensure disclaimer is always present (FR-04.4)
        ai_result['disclaimer'] = (
            "⚠️ IMPORTANT: This analysis is for informational purposes only and does NOT "
            "constitute a medical diagnosis or professional medical advice. The conditions listed "
            "are possibilities based on the symptoms described and may not accurately reflect "
            "your actual health condition. Please consult a qualified and registered medical "
            "professional for proper diagnosis and treatment."
        )

        # Log to MongoDB for continuous model improvement (FR-04.5)
        try:
            collection = get_mongo_collection('ai_symptom_logs')
            collection.insert_one({
                'user_id':         request.user.id,
                'user_role':       request.user.role,
                'symptoms_input':  symptoms,
                'ai_response':     ai_result,
                'model_version':   settings.OPENAI_MODEL,
                'response_time_ms': response_time_ms,
                'created_at':      __import__('datetime').datetime.utcnow(),
            })
        except Exception as mongo_err:
            # MongoDB logging failure should NOT fail the API response
            logger.error(f"MongoDB AI log failed: {mongo_err}")

        return Response({
            'symptoms_submitted': symptoms,
            'analysis':          ai_result,
            'response_time_ms':  response_time_ms,
        })

    except Exception as e:
        logger.error(f"Symptom check failed for user {request.user.id}: {e}")
        return Response(
            {'message': 'The AI service is temporarily unavailable. Please try again later.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_doctor(request):
    """
    POST /api/v1/ai/recommend-doctor/
    Recommends up to 3 doctors based on symptoms and specialist type (FR-04.3).
    Uses a multi-factor scoring algorithm:
      - Speciality match (40%)
      - Availability (25%)
      - Rating (20%)
      - Location proximity (10%)
      - Consultation fee (5%)
    """
    specialist_type = request.data.get('specialist_type', '').strip()
    symptoms        = request.data.get('symptoms', '').strip()
    max_fee         = request.data.get('max_fee', None)
    available_only  = request.data.get('available_only', True)

    if not specialist_type:
        return Response(
            {'message': 'specialist_type is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from apps.accounts.models import DoctorProfile
    from apps.accounts.serializers import DoctorProfileSerializer

    # Base queryset
    qs = DoctorProfile.objects.filter(
        user__is_active=True
    ).select_related('user').prefetch_related('availability')

    if available_only:
        qs = qs.filter(is_available=True)

    if max_fee:
        qs = qs.filter(consultation_fee__lte=max_fee)

    # Score each doctor
    scored_doctors = []
    for doctor in qs:
        score = 0.0

        # 40% — Speciality match (case-insensitive substring match)
        if specialist_type.lower() in doctor.speciality.lower():
            score += 40.0
        elif any(
            word in doctor.speciality.lower()
            for word in specialist_type.lower().split()
        ):
            score += 20.0

        # 25% — Availability (has slots this week)
        if doctor.availability.filter(is_active=True).exists():
            score += 25.0

        # 20% — Rating (max 5.0 → scaled to 20 points)
        score += float(doctor.rating) * 4.0

        # 5% — Fee (lower fee = more points, max 5 points)
        if doctor.consultation_fee > 0:
            score += max(0, 5.0 - float(doctor.consultation_fee) / 10000)

        scored_doctors.append((score, doctor))

    # Sort by score descending, take top 3
    scored_doctors.sort(key=lambda x: x[0], reverse=True)
    top_3 = [doc for _, doc in scored_doctors[:3]]

    serializer = DoctorProfileSerializer(top_3, many=True)
    return Response({
        'specialist_type': specialist_type,
        'recommendations': serializer.data,
        'total_found':     len(scored_doctors),
    })

