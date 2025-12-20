from django.conf import settings
from django.db import models
from visits.models import Visit

class LabTest(models.Model):
    name = models.CharField(max_length=180, unique=True)  # e.g. Full Blood Count (FBC)
    category = models.CharField(max_length=80, blank=True) # Haematology, Chemistry
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class LabRequest(models.Model):
    class Priority(models.TextChoices):
        ROUTINE = "ROUTINE", "Routine"
        URGENT = "URGENT", "Urgent"

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        SAMPLE_COLLECTED = "SAMPLE_COLLECTED", "Sample Collected"
        RESULT_READY = "RESULT_READY", "Result Ready"

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="lab_requests")
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.ROUTINE)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.REQUESTED)

    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.visit.visit_number} - {self.test.name}"

class LabResult(models.Model):
    lab_request = models.OneToOneField(LabRequest, on_delete=models.CASCADE, related_name="result")
    result_text = models.TextField()  # keep simple for now (later JSON per test type)
    remarks = models.CharField(max_length=255, blank=True)

    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

