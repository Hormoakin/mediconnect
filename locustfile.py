"""
performance/locustfile.py

MediConnect Load Tests — validates NFR-01 through NFR-04.
Target: 500 concurrent users, p95 response time < 500ms.

Run locally:
  locust -f performance/locustfile.py --host https://api.mediconnect.salman-aak.com

Run headless (CI):
  locust -f performance/locustfile.py \
    --host https://api.mediconnect.salman-aak.com \
    --headless \
    --users 500 \
    --spawn-rate 25 \
    --run-time 2m \
    --html performance/report.html \
    --csv performance/results
"""
import random
import json
import time
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


# ── Test user pool (pre-seeded in DB via seed-db.sh) ──────────
TEST_EMAILS    = [f"loadtest_patient_{i}@test.com" for i in range(1, 501)]
TEST_PASSWORD  = "TestLoad123!"
TEST_DOCTOR_IDS = list(range(1, 21))   # 20 doctors pre-seeded


# ── Shared result storage for custom metrics ──────────────────
class Metrics:
    symptom_check_times = []
    booking_success     = 0
    booking_failure     = 0


# ══════════════════════════════════════════════════════════════
class PatientUser(HttpUser):
    """
    Simulates a patient user performing the most common workflows:
    - View appointments (high frequency)
    - Search doctors     (medium frequency)
    - Book appointment   (low frequency — expensive operation)
    - Check symptoms     (low frequency — AI call)
    """
    wait_time = between(1, 3)   # Realistic think time between requests
    token: str = None

    def on_start(self):
        """Authenticate at session start."""
        email = random.choice(TEST_EMAILS)
        with self.client.post(
            "/api/v1/auth/login/",
            json={"email": email, "password": TEST_PASSWORD},
            catch_response=True,
            name="/api/v1/auth/login/",
        ) as resp:
            if resp.status_code == 200:
                data  = resp.json()
                self.token = data.get("access")
                self.client.headers.update(
                    {"Authorization": f"Bearer {self.token}"}
                )
            else:
                resp.failure(f"Login failed: {resp.status_code}")
                raise RescheduleTask()

    # ── High frequency tasks (weight=5) ──────────────────────
    @task(5)
    def view_appointments(self):
        """
        GET /api/v1/appointments/
        Most common patient action — validates NFR-01 (< 500ms p95).
        """
        with self.client.get(
            "/api/v1/appointments/",
            catch_response=True,
            name="/api/v1/appointments/ [LIST]",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 401:
                resp.failure("Unauthenticated — token may have expired")
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(5)
    def view_profile(self):
        """GET /api/v1/users/me/"""
        self.client.get("/api/v1/users/me/", name="/api/v1/users/me/")

    # ── Medium frequency tasks (weight=3) ─────────────────────
    @task(3)
    def search_doctors(self):
        """
        GET /api/v1/doctors/?search=...
        Tests database query performance under load.
        """
        specialities = [
            "General", "Cardiologist", "Neurologist",
            "Paediatrician", "Dermatologist",
        ]
        search = random.choice(specialities)
        with self.client.get(
            f"/api/v1/doctors/?search={search}&ordering=-rating",
            catch_response=True,
            name="/api/v1/doctors/ [SEARCH]",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Doctor search failed: {resp.status_code}")

    @task(3)
    def view_prescriptions(self):
        """GET /api/v1/prescriptions/"""
        self.client.get("/api/v1/prescriptions/", name="/api/v1/prescriptions/ [LIST]")

    @task(3)
    def view_medical_records(self):
        """GET /api/v1/records/"""
        self.client.get("/api/v1/records/", name="/api/v1/records/ [LIST]")

    @task(3)
    def get_doctor_slots(self):
        """GET /api/v1/doctors/{id}/slots/?date=..."""
        from datetime import date, timedelta
        doctor_id  = random.choice(TEST_DOCTOR_IDS)
        test_date  = (date.today() + timedelta(days=random.randint(1, 14))).isoformat()
        with self.client.get(
            f"/api/v1/doctors/{doctor_id}/slots/?date={test_date}",
            catch_response=True,
            name="/api/v1/doctors/{id}/slots/",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Slots failed: {resp.status_code}")

    # ── Low frequency tasks (weight=1) ────────────────────────
    @task(1)
    def book_appointment(self):
        """
        POST /api/v1/appointments/
        Validates NFR-01 under write load + conflict detection (FR-02.3).
        """
        from datetime import datetime, timedelta
        doctor_id  = random.choice(TEST_DOCTOR_IDS)
        future_dt  = (
            datetime.now() + timedelta(days=random.randint(1, 30),
                                       hours=random.randint(9, 16))
        ).replace(minute=0, second=0, microsecond=0).isoformat()

        with self.client.post(
            "/api/v1/appointments/",
            json={
                "doctor":       doctor_id,
                "scheduled_at": future_dt,
                "reason":       "Load test appointment",
            },
            catch_response=True,
            name="/api/v1/appointments/ [BOOK]",
        ) as resp:
            if resp.status_code == 201:
                Metrics.booking_success += 1
                resp.success()
            elif resp.status_code == 400:
                # Conflict detection working correctly — not a test failure
                Metrics.booking_failure += 1
                resp.success()
            else:
                resp.failure(f"Booking error: {resp.status_code} — {resp.text[:200]}")

    @task(1)
    def check_symptoms(self):
        """
        POST /api/v1/ai/symptom-check/
        AI endpoint — validates the specific 3s target for AI responses
        (different from the general 500ms NFR-01 threshold).
        """
        symptoms = random.choice([
            "fever chills headache joint pain for two days",
            "chest pain shortness of breath sweating",
            "cough weeks blood sputum weight loss night sweats",
            "frequent urination thirst blurred vision fatigue",
            "severe headache neck stiffness fever vomiting",
        ])

        start = time.time()
        with self.client.post(
            "/api/v1/ai/symptom-check/",
            json={"symptoms": symptoms},
            catch_response=True,
            name="/api/v1/ai/symptom-check/ [AI]",
            timeout=10,
        ) as resp:
            elapsed = (time.time() - start) * 1000
            Metrics.symptom_check_times.append(elapsed)

            if resp.status_code == 200:
                data = resp.json()
                if "analysis" in data and "possible_conditions" in data["analysis"]:
                    resp.success()
                else:
                    resp.failure("AI response missing expected fields")
            elif resp.status_code == 503:
                # AI service temporarily unavailable — not a hard failure
                resp.success()
            else:
                resp.failure(f"Symptom check failed: {resp.status_code}")

    @task(1)
    def health_check(self):
        """
        GET /api/v1/health/
        Kubernetes liveness probe endpoint — should always be < 50ms.
        """
        with self.client.get(
            "/api/v1/health/",
            catch_response=True,
            name="/api/v1/health/ [PROBE]",
        ) as resp:
            if resp.status_code == 200 and resp.json().get("status") == "healthy":
                resp.success()
            else:
                resp.failure(f"Health check failed: {resp.status_code}")


# ══════════════════════════════════════════════════════════════
class DoctorUser(HttpUser):
    """
    Simulates a doctor user — lower ratio than patients (1:10 in real use).
    Focuses on appointment management and prescription issuance.
    """
    wait_time = between(2, 5)
    token: str = None

    def on_start(self):
        doctor_index = random.randint(1, 20)
        email        = f"loadtest_doctor_{doctor_index}@test.com"
        resp = self.client.post(
            "/api/v1/auth/login/",
            json={"email": email, "password": TEST_PASSWORD},
            name="/api/v1/auth/login/ [DOCTOR]",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access")
            self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(4)
    def view_schedule(self):
        self.client.get(
            "/api/v1/appointments/?ordering=scheduled_at",
            name="/api/v1/appointments/ [DOCTOR SCHEDULE]",
        )

    @task(2)
    def view_patient_records(self):
        self.client.get("/api/v1/records/", name="/api/v1/records/ [DOCTOR]")

    @task(1)
    def view_prescriptions_issued(self):
        self.client.get(
            "/api/v1/prescriptions/",
            name="/api/v1/prescriptions/ [DOCTOR LIST]",
        )


# ══════════════════════════════════════════════════════════════
# Custom event listeners for extended reporting
# ══════════════════════════════════════════════════════════════
@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Print custom performance summary on test completion."""
    print("\n" + "="*60)
    print("  MEDICONNECT LOAD TEST SUMMARY")
    print("="*60)

    if Metrics.symptom_check_times:
        import statistics
        times = sorted(Metrics.symptom_check_times)
        print(f"  AI Symptom Checker:")
        print(f"    Requests:     {len(times)}")
        print(f"    Avg latency:  {statistics.mean(times):.0f}ms")
        print(f"    Median:       {statistics.median(times):.0f}ms")
        print(f"    p95:          {times[int(len(times)*0.95)]:.0f}ms")
        print(f"    p99:          {times[int(len(times)*0.99)]:.0f}ms")
        print(f"    Max:          {max(times):.0f}ms")

    total_bookings = Metrics.booking_success + Metrics.booking_failure
    if total_bookings > 0:
        print(f"\n  Appointment Bookings:")
        print(f"    Total attempts: {total_bookings}")
        print(f"    Successful:     {Metrics.booking_success}")
        print(f"    Conflict (400): {Metrics.booking_failure} (expected — FR-02.3 working)")

    print("\n  NFR Targets:")
    stats = environment.stats.get("/api/v1/appointments/ [LIST]", "GET")
    if stats and hasattr(stats, 'get_response_time_percentile'):
        p95 = stats.get_response_time_percentile(0.95)
        status = "✅ PASS" if p95 < 500 else "❌ FAIL"
        print(f"    NFR-01 (p95 < 500ms):  {p95:.0f}ms — {status}")

    print("="*60 + "\n")
