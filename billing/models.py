from django.conf import settings
from django.db import models
from django.utils import timezone
from patients.models import Patient
from visits.models import Visit

import uuid


class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIAL = "PARTIAL", "Partially Paid"
        PAID = "PAID", "Paid"

    invoice_number = models.CharField(max_length=30, unique=True, blank=True)

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="invoices")
    visit = models.OneToOneField(Visit, on_delete=models.PROTECT, null=True, blank=True, related_name="invoice")
    hmo_name = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    patient_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # patient share
    hmo_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)      # HMO share

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class HMOState(models.TextChoices):
        OK = "OK", "OK"
        SUBMITTED = "SUBMITTED", "Submitted"
        DISPUTED = "DISPUTED", "Disputed"
        APPROVED = "APPROVED", "Approved"
        SETTLED = "SETTLED", "Settled"

    hmo_state = models.CharField(max_length=20, choices=HMOState.choices, default=HMOState.OK, blank=True)
    hmo_dispute_reason = models.TextField(blank=True)
    hmo_dispute_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hmo_last_reminded_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def _new_invoice_number() -> str:
        """
        Practically-unique invoice number:
        INV-YYYYMMDD-HHMMSS-XXXXXX
        """
        ts = timezone.now().strftime("%Y%m%d-%H%M%S")
        token = uuid.uuid4().hex[:6].upper()
        return f"INV-{ts}-{token}"

    def _ensure_unique_invoice_number(self):
        """
        If invoice_number is blank OR collides with an existing record,
        regenerate until unique.
        This fixes bad generators elsewhere (e.g. services) permanently.
        """
        # If blank, generate
        if not self.invoice_number:
            self.invoice_number = self._new_invoice_number()

        # If colliding (for a different row), regenerate
        while Invoice.objects.filter(invoice_number=self.invoice_number).exclude(pk=self.pk).exists():
            self.invoice_number = self._new_invoice_number()

    def save(self, *args, **kwargs):
        self._ensure_unique_invoice_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number or f"Invoice #{self.pk}"


class InvoiceLine(models.Model):
    class LineType(models.TextChoices):
        CONSULTATION = "CONSULTATION", "Consultation"
        LAB = "LAB", "Lab Test"
        DRUG = "DRUG", "Drug"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    line_type = models.CharField(max_length=20, choices=LineType.choices)
    description = models.CharField(max_length=255)

    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # split
    patient_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hmo_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.line_total = (self.qty * self.unit_price)
        super().save(*args, **kwargs)


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        POS = "POS", "POS"
        TRANSFER = "TRANSFER", "Transfer"
        HMO = "HMO", "HMO Settlement"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=80, blank=True)  # POS RRNs / transfer reference
    paid_at = models.DateTimeField(auto_now_add=True)

    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount}"


class HMOClaimBatch(models.Model):
    """
    Nigeria-friendly: claims are usually sent in batches (weekly/monthly).
    """
    hmo_name = models.CharField(max_length=120)
    period_start = models.DateField()
    period_end = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="DRAFT")  # DRAFT, SUBMITTED, PAID

    def __str__(self):
        return f"{self.hmo_name} ({self.period_start} to {self.period_end})"


class HMOClaimItem(models.Model):
    batch = models.ForeignKey(HMOClaimBatch, on_delete=models.CASCADE, related_name="items")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT)

    hmo_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    patient = models.CharField(max_length=255)
    hospital_number = models.CharField(max_length=30)
    visit_number = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    disputed = models.BooleanField(default=False)
    dispute_reason = models.TextField(blank=True)
    disputed_at = models.DateTimeField(null=True, blank=True)


class HMOFollowUp(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        REMINDED = "REINDED", "Reminded"
        ESCALATED = "ESCALATED", "Escalated"
        SETTLED = "SETTLED", "Settled"

    hmo_name = models.CharField(max_length=120)
    period_start = models.DateField()
    period_end = models.DateField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    last_action_at = models.DateTimeField(null=True, blank=True)
    next_follow_up_at = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hmo_name} ({self.period_start}–{self.period_end})"
