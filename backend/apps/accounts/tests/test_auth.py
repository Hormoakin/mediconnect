# ══════════════════════════════════════════════════════════════
# backend/apps/accounts/tests/test_auth.py
# Unit tests for authentication endpoints (FR-01)
# ══════════════════════════════════════════════════════════════
import pytest
from django.urls import reverse
from rest_framework import status
 
 
@pytest.mark.django_db
class TestUserRegistration:
 
    def test_patient_registration_succeeds(self, anon_client):
        url  = reverse('auth-register')
        data = {
            'email':            'newpatient@test.com',
            'username':         'newpatient',
            'full_name':        'Ada Obi',
            'phone':            '+2348012345678',
            'role':             'patient',
            'password':         'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }
        response = anon_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert response.data['user']['role'] == 'patient'
 
    def test_doctor_registration_succeeds(self, anon_client):
        url  = reverse('auth-register')
        data = {
            'email':            'newdoctor@test.com',
            'username':         'newdoctor',
            'full_name':        'Dr. Emeka Okafor',
            'phone':            '+2348023456789',
            'role':             'doctor',
            'password':         'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }
        response = anon_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
 
    def test_pharmacist_cannot_self_register(self, anon_client):
        """Pharmacist accounts must be created by admins (FR-01.1)."""
        url  = reverse('auth-register')
        data = {
            'email': 'pharmacist@test.com', 'username': 'pharma',
            'full_name': 'Test Pharma', 'phone': '+234800',
            'role': 'pharmacist', 'password': 'Pass123!', 'confirm_password': 'Pass123!',
        }
        response = anon_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
 
    def test_password_mismatch_returns_400(self, anon_client):
        url  = reverse('auth-register')
        data = {
            'email': 'mismatch@test.com', 'username': 'mismatch',
            'full_name': 'Test', 'phone': '+234800', 'role': 'patient',
            'password': 'Pass123!', 'confirm_password': 'Different123!',
        }
        response = anon_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
 
    def test_duplicate_email_returns_400(self, anon_client, patient_user):
        url  = reverse('auth-register')
        data = {
            'email':            patient_user.email,  # Already exists
            'username':         'different_username',
            'full_name':        'Test', 'phone': '+234800', 'role': 'patient',
            'password':         'StrongPass123!', 'confirm_password': 'StrongPass123!',
        }
        response = anon_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
 
    def test_weak_password_returns_400(self, anon_client):
        url  = reverse('auth-register')
        data = {
            'email': 'weak@test.com', 'username': 'weakpass',
            'full_name': 'Test', 'phone': '+234800', 'role': 'patient',
            'password': '123', 'confirm_password': '123',
        }
        response = anon_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
 
 
@pytest.mark.django_db
class TestLogin:
 
    def test_login_returns_jwt_with_role(self, anon_client, patient_user):
        url      = reverse('auth-login')
        response = anon_client.post(url, {
            'email': patient_user.email, 'password': 'TestPass123!'
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['role'] == 'patient'
 
    def test_wrong_password_returns_401(self, anon_client, patient_user):
        url      = reverse('auth-login')
        response = anon_client.post(url, {
            'email': patient_user.email, 'password': 'WrongPassword!'
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
 
    def test_inactive_user_cannot_login(self, anon_client, patient_user):
        patient_user.is_active = False
        patient_user.save()
        response = anon_client.post(reverse('auth-login'), {
            'email': patient_user.email, 'password': 'TestPass123!'
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
 
    def test_unauthenticated_access_to_protected_endpoint(self, anon_client):
        response = anon_client.get(reverse('appointment-list-create'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
 
 
@pytest.mark.django_db
class TestUserProfile:
 
    def test_get_own_profile(self, patient_client, patient_user):
        response = patient_client.get(reverse('user-me'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == patient_user.email
        assert response.data['role']  == 'patient'
 
    def test_update_own_profile(self, patient_client):
        response = patient_client.patch(reverse('user-me'), {
            'full_name': 'Updated Name', 'phone': '+2348099999999'
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['full_name'] == 'Updated Name'
 
