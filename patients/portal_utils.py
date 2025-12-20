from django.core.exceptions import PermissionDenied

def patient_only(user):
    if not user.is_authenticated or user.role != "patient":
        raise PermissionDenied("Patient access only")
