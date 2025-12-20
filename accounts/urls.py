from django.urls import path, include
from .views import RoleBasedLoginView

app_name = "accounts"

urlpatterns = [
    path("login/", RoleBasedLoginView.as_view(), name="login"),  # ✅ add ()
    path("", include("django.contrib.auth.urls")),  # keeps logout/password-reset URLs
]

