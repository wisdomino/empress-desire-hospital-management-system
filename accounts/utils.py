from django.core.exceptions import PermissionDenied

ALLOWED = {
    "frontdesk", "nurse", "doctor", "admin", "lab", "pharmacy", "billing", "patient"
}

def require_roles(user, roles):
    if not user.is_authenticated:
        raise PermissionDenied("Login required")
    if user.is_superuser:
        return
    if getattr(user, "role", None) not in roles:
        raise PermissionDenied("You do not have permission to access this page.")
