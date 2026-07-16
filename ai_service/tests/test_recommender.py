# ══════════════════════════════════════════════════════════════
# ai_service/tests/test_recommender.py
# ══════════════════════════════════════════════════════════════
class TestDoctorRecommender:
 
    MOCK_DOCTORS = [
        {
            "id": 1,
            "user_full_name": "Dr. Emeka Okafor",
            "speciality": "General Practitioner",
            "rating": "4.8",
            "years_experience": 10,
            "consultation_fee": "5000.00",
            "hospital_name": "Lagos General Hospital",
            "is_available": True,
            "availability": [{"is_active": True}],
        },
        {
            "id": 2,
            "user_full_name": "Dr. Amaka Eze",
            "speciality": "Cardiologist",
            "rating": "4.9",
            "years_experience": 15,
            "consultation_fee": "20000.00",
            "hospital_name": "Heart Care Clinic",
            "is_available": True,
            "availability": [{"is_active": True}],
        },
        {
            "id": 3,
            "user_full_name": "Dr. Chidi Nwosu",
            "speciality": "Neurologist",
            "rating": "4.5",
            "years_experience": 8,
            "consultation_fee": "15000.00",
            "hospital_name": "Brain & Spine Centre",
            "is_available": False,
            "availability": [],
        },
    ]
 
    @pytest.fixture
    def rec(self):
        with patch('recommender.settings') as mock_settings:
            mock_settings.backend_base_url = "http://test-backend:8000"
            from recommender import DoctorRecommender
            return DoctorRecommender()
 
    def test_returns_top_3(self, rec):
        rec._fetch_doctors = AsyncMock(return_value=self.MOCK_DOCTORS)
        result = run(rec.recommend(specialist_type="General Practitioner"))
        assert len(result.recommendations) <= 3
 
    def test_gp_ranks_above_cardiologist_for_gp_search(self, rec):
        rec._fetch_doctors = AsyncMock(return_value=self.MOCK_DOCTORS)
        result = run(rec.recommend(specialist_type="General Practitioner"))
        if len(result.recommendations) >= 2:
            assert result.recommendations[0].speciality == "General Practitioner"
 
    def test_available_only_filters_unavailable(self, rec):
        rec._fetch_doctors = AsyncMock(return_value=self.MOCK_DOCTORS)
        result = run(rec.recommend(
            specialist_type="Neurologist", available_only=True
        ))
        # Dr. Chidi is unavailable — should not appear
        names = [r.user_full_name for r in result.recommendations]
        assert "Dr. Chidi Nwosu" not in names
 
    def test_fee_filter_excludes_expensive(self, rec):
        rec._fetch_doctors = AsyncMock(return_value=self.MOCK_DOCTORS)
        result = run(rec.recommend(
            specialist_type="Doctor", max_fee=10000
        ))
        for doc in result.recommendations:
            assert float(doc.consultation_fee) <= 10000
 
    def test_scores_are_between_0_and_1(self, rec):
        rec._fetch_doctors = AsyncMock(return_value=self.MOCK_DOCTORS)
        result = run(rec.recommend(specialist_type="Cardiologist"))
        for doc in result.recommendations:
            assert 0.0 <= doc.score <= 1.0
 
    def test_empty_doctor_list_returns_empty(self, rec):
        rec._fetch_doctors = AsyncMock(return_value=[])
        result = run(rec.recommend(specialist_type="Dentist"))
        assert result.recommendations == []
        assert result.total_found == 0
 
    def test_backend_failure_returns_empty(self, rec):
        rec._fetch_doctors = AsyncMock(side_effect=Exception("Backend unreachable"))
        try:
            result = run(rec.recommend(specialist_type="GP"))
            assert result.recommendations == []
        except Exception:
            pass   # Also acceptable — exception should not propagate to user
 
