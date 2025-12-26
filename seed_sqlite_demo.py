# billing/management/commands/seed_demo_data.py

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4
from random import choice, randint, random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from patients.models import Patient
from visits.models import Visit

from billing.models import Invoice, Payment, HMOFollowUp
from billing.services import generate_invoice_for_visit

from pharmacy.models import Drug
from lab.models import LabTest, LabRequest, LabResult

# HMO model can be in hmo app or elsewhere depending on your project.
# Try both imports safely.
try:
    from hmo.models import HMO
except Exception:  # noqa
    try:
        from patients.models import HMO  # type: ignore
    except Exception:
        HMO = None  # type: ignore


def _mk_invoice_number() -> str:
    # Very low collision risk + unique per create
    return f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:8].upper()}"


class Command(BaseCommand):
    help = "Seed demo data for EDH HMS (SQLite-friendly)."

    def add_arguments(self, parser):
        parser.add_argument("--patients", type=int, default=25, help="Number of patients to create")
        parser.add_argument("--days", type=int, default=60, help="Spread data across the last N days")
        parser.add_argument("--flush", action="store_true", help="Delete existing demo data first (patients/visits/invoices/payments)")

    @transaction.atomic
    def handle(self, *args, **options):
        patients_n: int = options["patients"]
        days: int = options["days"]
        do_flush: bool = options["flush"]

        User = get_user_model()

        # ---------------------------
        # OPTIONAL FLUSH (SAFE-ish)
        # ---------------------------
        if do_flush:
            # Order matters because of FKs
            Payment.objects.all().delete()
            Invoice.objects.all().delete()
            # Visit has related lab + prescription via CASCADE in their apps
            Visit.objects.all().delete()
            Patient.objects.all().delete()
            HMOFollowUp.objects.all().delete()
            self.stdout.write(self.style.WARNING("Flushed Payments, Invoices, Visits, Patients, FollowUps."))

        # ---------------------------
        # USERS (roles)
        # ---------------------------
        def upsert_user(email: str, role: str, password: str = "Pass12345!"):
            u, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "role": role},
            )
            # make sure role/password are correct
            if getattr(u, "role", None) != role:
                u.role = role
            u.email = email
            u.set_password(password)
            u.is_active = True
            u.save()
            return u, created

        admin, _ = upsert_user("admin@edh.test", "admin")
        doctor, _ = upsert_user("doctor@edh.test", "doctor")
        billing_user, _ = upsert_user("billing@edh.test", "billing")
        frontdesk, _ = upsert_user("frontdesk@edh.test", "frontdesk")

        # ---------------------------
        # HMOs (optional model)
        # ---------------------------
        hmo_names = [
            "Hygeia HMO",
            "AXA Mansard HMO",
            "Reliance HMO",
            "Leadway Health",
            "Redcare HMO",
        ]
        hmos = []
        if HMO is not None:
            for name in hmo_names:
                h, _ = HMO.objects.get_or_create(
                    name=name,
                    defaults={
                        "contact_phone": "08000000000",
                        "email": "claims@example.com",
                        "address": "Port Harcourt",
                    },
                )
                hmos.append(h)

        # ---------------------------
        # DRUGS
        # ---------------------------
        if Drug.objects.count() < 10:
            defaults = [
                ("Paracetamol", "500mg", "Tablet", "300"),
                ("Amoxicillin", "500mg", "Capsule", "1500"),
                ("Ciprofloxacin", "500mg", "Tablet", "2000"),
                ("Metronidazole", "400mg", "Tablet", "1200"),
                ("Omeprazole", "20mg", "Capsule", "900"),
                ("Artemether/Lumefantrine", "20/120mg", "Tablet", "3500"),
            ]
            for name, strength, form, price in defaults:
                Drug.objects.get_or_create(
                    name=name,
                    strength=strength,
                    dosage_form=form,
                    defaults={"price": Decimal(price), "active": True},
                )

        drugs = list(Drug.objects.filter(active=True))

        # ---------------------------
        # LAB TESTS (NO PRICE FIELD)
        # ---------------------------
        if LabTest.objects.count() < 10:
            test_defaults = [
                ("Haematology", "Full Blood Count (FBC)"),
                ("Parasitology", "Malaria Parasite (MP)"),
                ("Serology", "HIV 1&2"),
                ("Chemistry", "Fasting Blood Sugar (FBS)"),
                ("Chemistry", "UEC"),
                ("Chemistry", "LFT"),
            ]
            for cat, name in test_defaults:
                LabTest.objects.get_or_create(
                    name=name,
                    defaults={"category": cat, "active": True},
                )

        tests = list(LabTest.objects.filter(active=True))

        # ---------------------------
        # PATIENTS + VISITS
        # ---------------------------
        blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        created_patients = 0
        created_visits = 0
        created_invoices = 0
        created_payments = 0
        created_labreq = 0
        created_rx = 0

        now = timezone.now()

        for _ in range(patients_n):
            is_hmo = random() < 0.45
            hmo_obj = choice(hmos) if (is_hmo and hmos) else None

            # Minimal, compatible patient fields based on your templates/views
            p = Patient.objects.create(
                first_name=f"Patient{uuid4().hex[:4]}",
                last_name=f"Demo{uuid4().hex[:4]}",
                other_names="",
                gender=choice(["Male", "Female"]),
                date_of_birth=(timezone.localdate() - timedelta(days=randint(365, 365 * 70))),
                phone=("080" + str(randint(10000000, 99999999))),
                email=f"p{uuid4().hex[:6]}@demo.test",
                address="Port Harcourt",
                blood_group=choice(blood_groups),
                is_hmo=is_hmo,
                hmo=hmo_obj if hmo_obj is not None else None,
                hmo_id_number=(f"HMO-{randint(10000000, 99999999)}" if is_hmo else ""),
                next_of_kin_name="Demo NOK",
                next_of_kin_phone=("080" + str(randint(10000000, 99999999))),
                allergies=choice(["", "No known allergies", "Penicillin allergy", "Asthma", "Hypertension"]),
            )
            created_patients += 1

            # 1–3 historical visits
            for __ in range(randint(1, 3)):
                created_at = now - timedelta(days=randint(0, days), hours=randint(0, 23))
                closed_at = created_at + timedelta(hours=randint(1, 6))

                visit = Visit.objects.create(
                    patient=p,
                    doctor=doctor,
                    status=Visit.Status.CLOSED,
                    visit_type=choice([Visit.VisitType.OPD, Visit.VisitType.EMERGENCY, Visit.VisitType.FOLLOWUP]),
                    chief_complaint=choice(["Fever", "Abdominal pain", "Headache", "Cough", "Body weakness"]),
                    diagnosis_primary=choice(["Malaria", "Gastritis", "Typhoid", "URTI", "Hypertension"]),
                    diagnosis_secondary="",
                    treatment_plan="Hydration, rest, meds as prescribed.",
                    doctor_notes="Demo notes.",
                    closed_at=closed_at,
                )

                # inline vitals on Visit model (matches your Visit fields)
                visit.weight_kg = Decimal(randint(10, 95))
                visit.height_cm = Decimal(randint(90, 190))
                visit.temperature_c = Decimal(str(round(36 + random() * 3, 1)))
                visit.pulse_bpm = randint(60, 120)
                visit.bp_systolic = randint(90, 160)
                visit.bp_diastolic = randint(60, 110)
                visit.resp_rate = randint(12, 30)
                visit.spo2 = randint(92, 100)
                visit.triage_note = "Demo triage note."
                visit.save()

                created_visits += 1

                # Prescriptions (0–3)
                from pharmacy.models import PrescriptionItem  # local import to avoid circulars

                for _rx in range(randint(0, 3)):
                    PrescriptionItem.objects.create(
                        visit=visit,
                        drug=choice(drugs),
                        dose="1 tab",
                        frequency="BD",
                        duration="3 days",
                        instructions="After meals",
                        status="PENDING",
                    )
                    created_rx += 1

                # Labs (0–2) + results
                for _lr in range(randint(0, 2)):
                    lr = LabRequest.objects.create(
                        visit=visit,
                        test=choice(tests),
                        priority=choice(["ROUTINE", "URGENT"]),
                        status="DONE",
                    )
                    LabResult.objects.create(
                        lab_request=lr,
                        result_text=choice(["Normal", "High", "Low", "Positive", "Negative"]),
                        remarks="",
                        performed_by=billing_user,
                    )
                    created_labreq += 1

                # Invoice generation (your service)
                inv = generate_invoice_for_visit(visit, user=billing_user)

                # If your service leaves invoice_number blank in some cases, force uniqueness:
                if not inv.invoice_number:
                    inv.invoice_number = _mk_invoice_number()
                    inv.save(update_fields=["invoice_number"])

                created_invoices += 1

                # Random patient payments (for patient share)
                if inv.patient_amount and inv.patient_amount > 0 and random() < 0.65:
                    amt = Decimal(str(round(float(inv.patient_amount) * random(), 2)))
                    if amt <= 0:
                        amt = min(inv.patient_amount, Decimal("2000.00"))

                    Payment.objects.create(
                        invoice=inv,
                        amount=amt,
                        method=choice([Payment.Method.CASH, Payment.Method.POS, Payment.Method.TRANSFER]),
                        reference=f"DEMO-{uuid4().hex[:8].upper()}",
                        received_by=billing_user,
                    )
                    created_payments += 1

                    # Recompute invoice totals if your service does that
                    generate_invoice_for_visit(visit, user=billing_user)

        # ---------------------------
        # FOLLOW-UP (one due, one future)
        # ---------------------------
        today = timezone.localdate()
        HMOFollowUp.objects.get_or_create(
            hmo_name=hmo_names[0],
            period_start=today - timedelta(days=30),
            period_end=today,
            defaults={
                "status": "REMINDED",
                "next_follow_up_at": today,  # due today
                "notes": "Demo follow-up due today.",
                "owner": billing_user,
                "last_action_at": timezone.now(),
            },
        )
        HMOFollowUp.objects.get_or_create(
            hmo_name=hmo_names[1],
            period_start=today - timedelta(days=30),
            period_end=today,
            defaults={
                "status": "OPEN",
                "next_follow_up_at": today + timedelta(days=7),
                "notes": "Demo follow-up next week.",
                "owner": billing_user,
                "last_action_at": timezone.now(),
            },
        )

        # ---------------------------
        # SUMMARY OUTPUT
        # ---------------------------
        self.stdout.write(self.style.SUCCESS("✅ Seed complete."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Patients: {created_patients}, Visits: {created_visits}, "
                f"Invoices: {created_invoices}, Payments: {created_payments}, "
                f"Rx: {created_rx}, LabReq: {created_labreq}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Demo logins:\n"
                "  admin@edh.test / Pass12345!\n"
                "  doctor@edh.test / Pass12345!\n"
                "  billing@edh.test / Pass12345!\n"
                "  frontdesk@edh.test / Pass12345!"
            )
        )
