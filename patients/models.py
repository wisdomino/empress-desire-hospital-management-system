from django.conf import settings
from django.db import models
from hmo.models import HMO

class Patient(models.Model):
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name="patient"
)
    hospital_number = models.CharField(max_length=20, unique=True, blank=True)

    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    other_names = models.CharField(max_length=60, blank=True)

    gender = models.CharField(max_length=10, choices=[("M","Male"),("F","Female")])
    date_of_birth = models.DateField(null=True, blank=True)

    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    passport_photo = models.ImageField(upload_to="patients/passports/", null=True, blank=True)

    is_hmo = models.BooleanField(default=False)
    hmo = models.ForeignKey(HMO, null=True, blank=True, on_delete=models.SET_NULL)
    hmo_id_number = models.CharField(max_length=60, blank=True)

    next_of_kin_name = models.CharField(max_length=120, blank=True)
    next_of_kin_phone = models.CharField(max_length=30, blank=True)

    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hospital_number} - {self.last_name} {self.first_name}"

