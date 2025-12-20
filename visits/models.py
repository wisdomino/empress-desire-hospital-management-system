from django.conf import settings
from django.db import models
from patients.models import Patient


class Visit(models.Model):
    class VisitType(models.TextChoices):
        OPD = "OPD", "Outpatient"
        EMERGENCY = "ER", "Emergency"
        FOLLOWUP = "FU", "Follow-up"
        ADMISSION = "ADM", "Admission"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        WAITING_DOCTOR = "WAITING_DOCTOR", "Waiting Doctor"
        IN_CONSULT = "IN_CONSULT", "In Consultation"
        CLOSED = "CLOSED", "Closed"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="visits")
    visit_number = models.CharField(max_length=30, unique=True, blank=True)

    visit_type = models.CharField(max_length=10, choices=VisitType.choices, default=VisitType.OPD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Assigned doctor (optional at this stage)
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_visits",
    )

    # --- CONSULTATION (Doctor) ---
    chief_complaint = models.CharField(max_length=255, blank=True)
    history_of_present_illness = models.TextField(blank=True)
    examination = models.TextField(blank=True)

    diagnosis_primary = models.CharField(max_length=255, blank=True)
    diagnosis_secondary = models.CharField(max_length=255, blank=True)
    treatment_plan = models.TextField(blank=True)

    doctor_notes = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # --- VITALS (captured by front desk / nurse) ---
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    bp_systolic = models.IntegerField(null=True, blank=True)
    bp_diastolic = models.IntegerField(null=True, blank=True)

    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    pulse_bpm = models.IntegerField(null=True, blank=True)
    resp_rate = models.IntegerField(null=True, blank=True)
    spo2 = models.IntegerField(null=True, blank=True)

    triage_note = models.TextField(blank=True)

    def __str__(self):
        # NOTE: this assumes Patient has `hospital_number`.
        return f"{self.visit_number} - {self.patient.hospital_number}"

    def has_vitals(self) -> bool:
        return any([
            self.bp_systolic, self.bp_diastolic, self.temperature_c, self.pulse_bpm,
            self.resp_rate, self.spo2, self.weight_kg, self.height_cm
        ])
