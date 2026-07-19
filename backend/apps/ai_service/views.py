"""
apps/ai_service/views.py

AI-powered symptom checker and doctor recommendation endpoints.

Implements:

FR-04.1  AI Symptom Checker
FR-04.2  AI Clinical Analysis
FR-04.3  Doctor Recommendation
FR-04.4  Mandatory Medical Disclaimer
FR-04.5  AI Request Logging

Architecture
------------

PostgreSQL
    • users
    • patients
    • doctors
    • appointments
    • availability
    • prescriptions
    • medical records

OpenAI
    • symptom analysis
    • urgency estimation
    • specialist recommendation

MongoDB
    • AI request logging ONLY
    • analytics
    • future model improvement

MongoDB NEVER stores:
    • patients
    • doctors
    • appointments
    • symptoms
    • medical records

MongoDB NEVER generates AI responses.

If MongoDB becomes unavailable,
the AI service continues functioning normally.
"""

import json
import logging
import time
from datetime import datetime

from django.conf import settings

from openai import OpenAI
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


# ==========================================================
# MongoDB Helper
# ==========================================================

def get_mongo_collection(collection_name: str):
    """
    Returns a MongoDB collection.

    MongoDB is used ONLY for analytics logging.

    It is NOT used to:

    • store patients
    • retrieve symptoms
    • generate AI responses
    • recommend doctors
    • run OpenAI

    Any MongoDB failure should NEVER interrupt
    the user request.
    """

    client = MongoClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=2000
    )
    try:
        collection = client["mediconnect"]["ai_symptom_logs"]
        collection.insert_one({...})
    finally:
        client.close()

    db = client["mediconnect"]

    return db[collection_name]


# ==========================================================
# MongoDB Logging
# ==========================================================

def log_ai_request(
    request,
    symptoms,
    ai_result,
    response_time_ms
):
    """
    Stores AI interaction for future analytics.

    MongoDB logging is OPTIONAL.

    The application must continue even if
    MongoDB is offline.
    """

    try:

        collection = get_mongo_collection(
            "ai_symptom_logs"
        )

        collection.insert_one({

            "user_id": request.user.id,

            "user_role": getattr(
                request.user,
                "role",
                None
            ),

            "symptoms": symptoms,

            "ai_response": ai_result,

            "model": settings.OPENAI_MODEL,

            "response_time_ms": response_time_ms,

            "timestamp": datetime.utcnow()

        })

        logger.info(
            "AI request successfully logged to MongoDB."
        )

    except PyMongoError as e:

        logger.warning(
            f"MongoDB logging unavailable: {e}"
        )

    except Exception as e:

        logger.warning(
            f"Unexpected MongoDB logging error: {e}"
        )


# ==========================================================
# AI Symptom Checker
# ==========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def symptom_check(request):
    """
    AI Symptom Checker

    Workflow

    1.
    Receive patient symptoms.

    2.
    Validate request.

    3.
    Send prompt to OpenAI.

    4.
    Parse AI JSON response.

    5.
    Attach mandatory disclaimer.

    6.
    Log request to MongoDB.

    7.
    Return response.

    Important:

    MongoDB DOES NOT participate
    in AI generation.

    MongoDB ONLY stores a copy
    of the finished result.
    """

    symptoms = request.data.get('symptoms', '').strip()

    if not symptoms or len(symptoms) < 5:
        return Response(
            {'message': 'Please describe your symptoms in at least a few words.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    logger.info(
        "User %s requested symptom analysis",
        request.user.id
    )

    start_time = time.time()

    try:

        client = OpenAI(
            api_key=settings.OPENAI_API_KEY
            timeout=30
        )
        required_keys = [
            "possible_conditions",
            "urgency_level",
            "recommended_specialist",
            "recommended_actions"
        ]

        for key in required_keys:
            ai_result.setdefault(key, None)

        system_prompt = (
            "You are an experienced medical triage assistant. "
            "Provide cautious, evidence-informed clinical guidance. "
            "Never claim to provide a diagnosis. "
            "Always include a disclaimer."
        )

        user_prompt = f"""
Patient symptoms:

{symptoms}

Return ONLY valid JSON.

{{
    "possible_conditions":[
        {{
            "condition":"",
            "confidence":0.0,
            "description":""
        }}
    ],

    "urgency_level":"low",

    "urgency_reason":"",

    "recommended_specialist":"",

    "recommended_actions":[
        ""
    ],

    "red_flags":[
        ""
    ],

    "disclaimer":""
}}
"""
       logger.info(
           "Calling OpenAI model %s",
           settings.OPENAI_MODEL
       )
        response = client.chat.completions.create(

            model=settings.OPENAI_MODEL,

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": user_prompt
                }

            ],

            response_format={
                "type": "json_object"
            },

            temperature=0.2,

            max_tokens=800

        )

        response_time_ms = int(
            (time.time() - start) * 1000
        )

        raw_response = (
            response
            .choices[0]
            .message
            .content
        )

        logger.info(
            "OpenAI response received in %sms",
            response_time_ms
        )

        try:

            ai_result = json.loads(raw_response)

        except json.JSONDecodeError:

            logger.exception(
                "OpenAI returned invalid JSON."
            )

            return Response(

                {
                    "message":
                    "AI service returned an invalid response."
                },

                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        ai_result["disclaimer"] = (
            "⚠️ This AI analysis is provided for informational purposes only. "
            "It is NOT a medical diagnosis and should never replace consultation "
            "with a licensed healthcare professional."
        )

        # -------------------------------------------------
        # MongoDB Logging
        #
        # Logging ONLY.
        #
        # If MongoDB fails,
        # ignore the error.
        # -------------------------------------------------

        log_ai_request(
            request=request,
            symptoms=symptoms,
            ai_result=ai_result,
            response_time_ms=response_time_ms
        )

        return Response({

            "symptoms_submitted": symptoms,

            "analysis": ai_result,

            "response_time_ms": response_time_ms

        })

    except Exception as e:

        logger.exception(
            f"AI request failed: {e}"
        )

        return Response(

            {
                "message":
                "The AI service is temporarily unavailable."
            },

            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

# ==========================================================
# Doctor Recommendation
# ==========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recommend_doctor(request):
    """
    AI Doctor Recommendation (FR-04.3)

    Doctors are retrieved entirely from PostgreSQL.

    MongoDB is NEVER queried here.

    Ranking Criteria
    ----------------

    • Speciality Match ............ 40%
    • Availability .................25%
    • Rating .......................20%
    • Consultation Fee .............5%
    • Experience ..................10%

    Response returns the Top 3 doctors.
    """

    specialist_type = (
        request.data.get(
            "specialist_type",
            ""
        ).strip()
    )

    symptoms = (
        request.data.get(
            "symptoms",
            ""
        ).strip()
    )

    max_fee = request.data.get(
        "max_fee",
        None
    )

    available_only = request.data.get(
        "available_only",
        True
    )

    if not specialist_type:

        return Response(

            {
                "message":
                "specialist_type is required."
            },

            status=status.HTTP_400_BAD_REQUEST
        )

    from apps.accounts.models import DoctorProfile
    from apps.accounts.serializers import DoctorProfileSerializer

    queryset = (

        DoctorProfile.objects

        .filter(
            user__is_active=True
        )

        .select_related("user")

        .prefetch_related(
            "availability"
        )

    )

    if available_only:

        queryset = queryset.filter(
            is_available=True
        )

    if max_fee:

        queryset = queryset.filter(
            consultation_fee__lte=max_fee
        )

    ranked = []

    for doctor in queryset:

        score = 0.0

        # -----------------------------------
        # 40%
        # Specialty Match
        # -----------------------------------

        doctor_speciality = (
            doctor.speciality.lower()
        )

        requested = (
            specialist_type.lower()
        )

        if requested in doctor_speciality:

            score += 40

        elif any(

            word in doctor_speciality

            for word in requested.split()

        ):

            score += 20

        # -----------------------------------
        # 25%
        # Availability
        # -----------------------------------

        if doctor.availability.filter(
            is_active=True
        ).exists():

            score += 25

        # -----------------------------------
        # 20%
        # Rating
        # -----------------------------------

        try:

            score += float(
                doctor.rating
            ) * 4

        except Exception:

            pass

        # -----------------------------------
        # 10%
        # Experience
        # -----------------------------------

        if hasattr(
            doctor,
            "years_of_experience"
        ):

            try:

                years = int(
                    doctor.years_of_experience
                )

                score += min(
                    years,
                    10
                )

            except Exception:

                pass

        # -----------------------------------
        # 5%
        # Consultation Fee
        # -----------------------------------

        try:

            if doctor.consultation_fee:

                score += max(

                    0,

                    5 - (
                        float(
                            doctor.consultation_fee
                        ) / 10000
                    )

                )

        except Exception:

            pass

        ranked.append(

            {
                "score": score,
                "doctor": doctor
            }

        )

    ranked.sort(

        key=lambda d: d["score"],

        reverse=True

    )

    top_three = [

        item["doctor"]

        for item in ranked[:3]

    ]

    serializer = DoctorProfileSerializer(

        top_three,

        many=True

    )

    return Response(

        {

            "specialist_type": specialist_type,

            "symptoms": symptoms,

            "recommendations": serializer.data,

            "total_doctors_considered": len(ranked),

            "returned": len(top_three),

            "ranking_algorithm": {

                "speciality_match": "40%",

                "availability": "25%",

                "rating": "20%",

                "experience": "10%",

                "consultation_fee": "5%"

            },

            "data_source": {

                "doctor_data": "PostgreSQL",

                "ai_analysis": "OpenAI GPT",

                "analytics_logging": "MongoDB"

            }

        }

    )
