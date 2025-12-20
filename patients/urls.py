from django.urls import path, include
from . import views

app_name = "patients"

urlpatterns = [
    path("", views.patient_list, name="patient_list"),
    path("new/", views.patient_create, name="patient_create"),
    path("<int:pk>/", views.patient_detail, name="patient_detail"),
    path("portal/", include("patients.portal_urls")),
    path("portal/", views.patient_portal, name="patient_portal"),
]
