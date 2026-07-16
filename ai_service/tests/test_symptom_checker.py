# ══════════════════════════════════════════════════════════════
# ai_service/tests/test_symptom_checker.py
# Tests for the AI symptom analysis pipeline.
# GPT-4 and MongoDB are mocked so tests run in CI without
# real API keys or a live database.
# ══════════════════════════════════════════════════════════════
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
 
 
@pytest.fixture
def checker():
    """Create a SymptomChecker with mocked external dependencies."""
    with patch('symptom_checker.MongoClient') as mock_mongo, \
         patch('symptom_checker.AsyncOpenAI') as mock_openai:
 
        mock_mongo.return_value.admin.command.return_value = True
        mock_openai.return_value = AsyncMock()
 
        from symptom_checker import SymptomChecker
        sc = SymptomChecker()
        sc._mongo_client = None   # Disable logging in unit tests
        return sc
 
 
def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
 
 
class TestSymptomClassifier:
 
    def test_returns_top_3_conditions(self, checker):
        conditions = checker._classify_symptoms("fever headache joint pain fatigue")
        assert len(conditions) <= 3
        assert len(conditions) >= 1
 
    def test_confidence_scores_between_0_and_1(self, checker):
        conditions = checker._classify_symptoms("cough chest pain shortness of breath")
        for c in conditions:
            assert 0.0 <= c.confidence <= 1.0
 
    def test_malaria_pattern_detected(self, checker):
        """Nigerian-context: malaria should rank high for classic triad."""
        conditions = checker._classify_symptoms("fever chills headache joint pain")
        top_condition = conditions[0].condition if conditions else ""
        # Malaria or similar febrile illness should rank in top results
        top_names = [c.condition.lower() for c in conditions]
        assert any(
            "malaria" in name or "fever" in name or "typhoid" in name
            for name in top_names
        ), f"Expected malaria/fever pattern, got: {top_names}"
 
    def test_cardiac_pattern_detected(self, checker):
        conditions = checker._classify_symptoms("chest pain shortness of breath sweating arm pain")
        top_names  = [c.condition.lower() for c in conditions]
        assert any("cardiac" in n or "heart" in n for n in top_names), \
            f"Cardiac pattern not detected: {top_names}"
 
    def test_short_input_does_not_crash(self, checker):
        conditions = checker._classify_symptoms("pain")
        assert isinstance(conditions, list)
 
    def test_all_conditions_have_names(self, checker):
        conditions = checker._classify_symptoms("headache nausea vomiting")
        for c in conditions:
            assert c.condition and len(c.condition) > 0
 
    def test_specialist_map_populated(self, checker):
        assert len(checker._specialists) > 0
        assert "Malaria" in checker._specialists
        assert checker._specialists["Malaria"] == "General Practitioner"
 
 
class TestGPT4Enhancement:
 
    def test_full_analyse_returns_response(self, checker):
        mock_gpt_response = {
            "urgency_level":          "medium",
            "urgency_reason":         "Symptoms may indicate a febrile illness requiring prompt attention.",
            "recommended_specialist": "General Practitioner",
            "recommended_actions":    ["Visit a clinic", "Stay hydrated", "Take paracetamol for fever"],
            "red_flags":              [],
            "condition_descriptions": {
                "Malaria": "A parasitic infection transmitted by mosquitoes, common in Nigeria."
            }
        }
 
        checker._enhance_with_gpt4 = AsyncMock(return_value=mock_gpt_response)
 
        result = run(checker.analyse(symptoms="fever chills headache joint pain"))
 
        assert result.symptoms_submitted == "fever chills headache joint pain"
        assert len(result.analysis.possible_conditions) >= 1
        assert result.analysis.urgency_level.value in ("low", "medium", "high", "emergency")
        assert result.analysis.disclaimer != ""
        assert "NOT" in result.analysis.disclaimer or "not" in result.analysis.disclaimer
        assert result.response_time_ms >= 0
 
    def test_disclaimer_always_present(self, checker):
        """FR-04.4: disclaimer must ALWAYS be included."""
        checker._enhance_with_gpt4 = AsyncMock(return_value={
            "urgency_level": "low",
            "urgency_reason": "Minor symptoms",
            "recommended_specialist": "General Practitioner",
            "recommended_actions": ["Rest"],
            "red_flags": [],
            "condition_descriptions": {},
        })
 
        result = run(checker.analyse(symptoms="mild headache"))
        assert result.analysis.disclaimer
        assert len(result.analysis.disclaimer) > 50
 
    def test_gpt4_failure_falls_back_to_ml_only(self, checker):
        """System must be resilient to OpenAI API failures."""
        checker._enhance_with_gpt4 = AsyncMock(
            side_effect=Exception("OpenAI API unavailable")
        )
 
        result = run(checker.analyse(symptoms="fever headache fatigue"))
        # Should still return a valid response from ML stage alone
        assert result is not None
        assert len(result.analysis.possible_conditions) >= 1
        assert result.analysis.disclaimer
 
    def test_model_version_in_response(self, checker):
        checker._enhance_with_gpt4 = AsyncMock(return_value={
            "urgency_level": "low",
            "urgency_reason": "Minor",
            "recommended_specialist": "GP",
            "recommended_actions": [],
            "red_flags": [],
            "condition_descriptions": {},
        })
        result = run(checker.analyse(symptoms="mild cold runny nose"))
        assert result.model_version  # Should not be empty
 
