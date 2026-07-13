"""
apps/accounts/permissions.py
Role-Based Access Control permission classes.
These are applied at the view level (Section 3.8.1) to enforce
that only the correct user role can access each endpoint.
"""
from rest_framework.permissions import BasePermission, IsAuthenticated


class IsPatient(BasePermission):
    """Allow access only to authenticated users with role=patient."""
    message = 'Access restricted to patients.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'patient'
        )


class IsDoctor(BasePermission):
    """Allow access only to authenticated users with role=doctor."""
    message = 'Access restricted to doctors.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'doctor'
        )


class IsPharmacist(BasePermission):
    """Allow access only to authenticated users with role=pharmacist."""
    message = 'Access restricted to pharmacists.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'pharmacist'
        )


class IsAdminRole(BasePermission):
    """Allow access only to authenticated users with role=admin."""
    message = 'Access restricted to administrators.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsDoctorOrAdmin(BasePermission):
    """Allow access to doctors or administrators."""
    message = 'Access restricted to doctors or administrators.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ('doctor', 'admin')
        )


class IsPatientOrDoctor(BasePermission):
    """Allow access to patients or doctors (e.g. shared endpoints)."""
    message = 'Access restricted to patients or doctors.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ('patient', 'doctor')
        )


class IsOwnerOrDoctor(BasePermission):
    """
    Object-level permission: allow access if the requesting user
    is the owner of the object (patient viewing own record)
    OR is a doctor.
    """
    message = 'You do not have permission to access this record.'

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'doctor':
            return True
        # Check if the object has a patient/user field
        if hasattr(obj, 'patient'):
            return obj.patient == request.user or obj.patient_id == request.user.id
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
