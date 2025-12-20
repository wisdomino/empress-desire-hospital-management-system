from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        FRONTDESK = "frontdesk", "Front Desk"
        DOCTOR = "doctor", "Doctor"
        NURSE = "nurse", "Nurse"
        PHARMACY = "pharmacy", "Pharmacy"
        LAB = "lab", "Lab"
        BILLING = "billing", "Billing"
        PATIENT = "patient", "Patient"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.FRONTDESK)
