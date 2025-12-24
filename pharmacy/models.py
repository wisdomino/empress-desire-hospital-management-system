from django.db import models
from visits.models import Visit

class Drug(models.Model):
    name = models.CharField(max_length=180)
    strength = models.CharField(max_length=80, blank=True)   # e.g. 500mg
    dosage_form = models.CharField(max_length=80, blank=True) # tablet, syrup
    active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        s = f"{self.name}"
        if self.strength: s += f" {self.strength}"
        if self.dosage_form: s += f" ({self.dosage_form})"
        return s

class PrescriptionItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DISPENSED = "DISPENSED", "Dispensed"
        CANCELLED = "CANCELLED", "Cancelled"

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="prescriptions")
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT)
    dose = models.CharField(max_length=80, blank=True)       # 1 tab
    frequency = models.CharField(max_length=80, blank=True)  # bd, tds
    duration = models.CharField(max_length=80, blank=True)   # 5 days
    instructions = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.visit.visit_number} - {self.drug}"
