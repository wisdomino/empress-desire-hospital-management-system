from django.urls import path
from . import portal_views

app_name = "portal"

urlpatterns = [
    path("dashboard/", portal_views.patient_dashboard, name="dashboard"),
    path("visit/<int:visit_id>/", portal_views.patient_visit_detail, name="visit_detail"),
]
