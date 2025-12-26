from decimal import Decimal
from random import choice, randint, random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from faker import Faker

from patients.models import Patient, HMO
from visits.models import Visit
from pharmacy.models import Drug, PrescriptionItem
from lab.models import LabTest, LabRequest, LabResult

from billing.services import generate_invoice_for_visit
from billing.models import Payment, HMOClaimBatch, HMOClaimItem, HMOFollowUp

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Seed demo dataset for EDH HMS"

    def add_arguments(self, parser):
        parser.add_argument("--patients", type=int, default=50)
        parser.add_argument("--days", type=int, default=60)

    def handle(self, *args, **opts):
        patients_n = opts["patients"]
        days = opts["days"]
        now = timezone.now()

        # -------------------------------------------------
        # USERS
        # -------------------------------------------------
        def ensure_user(username, role, password="Pass12345!"):
            u, created = User.objects.get_or_create(
                username=username,
                defaults={"role": role, "email": username},
            )
            if created:
                u.set_password(password)
                u.save()
            return u

        admin = ensure_user("admin@edh.test", "admin")
        doctor = ensure_user("doctor@edh.test", "doctor")
        billing = ensure_user("billing@edh.test", "billing")
        frontdesk = ensure_user("frontdesk@edh.test", "frontdesk")

        # -------------------------------------------------
        # HMOs
        # -------------------------------------------------
        hmo_names = [
            "Hygeia HMO",
            "AXA Mansard HMO",
            "Reliance HMO",
            "Leadway Health",
            "Redcare HMO",
        ]

        hmos = []
        for name in hmo_names:
            h, _ = HMO.objects.get_or_create(
                name=name,
                defaults={"contact_phone": "08000000000"},
            )
            hmos.append(h)

        # -------------------------------------------------
        # DRUGS
        # -------------------------------------------------
        if Drug.objects.count() < 10:
            for name, strength, form, price in [
                ("Paracetamol", "500mg", "Tablet", "300"),
                ("Amoxicillin", "500mg", "Capsule", "1500"),
                ("Ciprofloxacin", "500mg", "Tablet", "2000"),
                ("Metronidazole", "400mg", "Tablet", "1200"),
                ("Omeprazole", "20mg", "Capsule", "900"),
                ("Artemether/Lumefantrine", "20/120mg", "Tablet", "3500"),
            ]:
                Drug.objects.get_or_create(
                    name=name,
                    strength=strength,
                    dosage_form=form,
                    defaults={"price": Decimal(price), "active": True},
                )

        # -------------------------------------------------
# LAB TESTS 
# -------------------------------------------------
if LabTest.objects.count() < 10:
    for cat, name in [
        ("Haematology", "Full Blood Count (FBC)"),
        ("Parasitology", "Malaria Parasite (MP)"),
        ("Serology", "HIV 1&2"),
        ("Chemistry", "Fasting Blood Sugar (FBS)"),
        ("Chemistry", "UEC"),
        ("Chemistry", "LFT"),
    ]:
        LabTest.objects.get_or_create(
            name=name,
            defaults={
                "category": cat,
                "active": True,
            },
        )

                # -------------------------------------------------
        # PATIENTS + VISITS
        # -------------------------------------------------
        created_patients = 0
        blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

        for _ in range(patients_n):
            is_hmo = random() < 0.45
            hmo = choice(hmos) if is_hmo else None

            p = Patient.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                other_names=fake.first_name() if random() < 0.35 else "",
                gender=choice(["Male", "Female"]),
                date_of_birth=fake.date_of_birth(minimum_age=1, maximum_age=80),

                phone=fake.msisdn()[:11],
                email=fake.email(),
                address=fake.address(),

                blood_group=choice(blood_groups),

                is_hmo=is_hmo,
                hmo=hmo,
                hmo_id_number=(
                    f"HMO-{fake.random_number(digits=8, fix_len=True)}"
                    if is_hmo else ""
                ),

                next_of_kin_name=fake.name(),
                next_of_kin_phone=fake.msisdn()[:11],

                allergies=choice([
                    "",
                    "No known allergies",
                    "Penicillin allergy",
                    "Asthma",
                    "Hypertension",
                    "Diabetes",
                ]),
            )
            created_patients += 1

            for _v in range(randint(1, 3)):
                created_at = now - timedelta(days=randint(0, days))

                visit = Visit.objects.create(
                    patient=p,
                    doctor=doctor,
                    status=Visit.Status.CLOSED,
                    created_at=created_at,
                    chief_complaint=choice(
                        ["Fever", "Abdominal pain", "Headache", "Cough"]
                    ),
                    diagnosis_primary=choice(
                        ["Malaria", "Gastritis", "Typhoid", "URTI"]
                    ),
                    closed_at=created_at + timedelta(hours=randint(1, 6)),
                )

                # -------------------------------
                # VITALS (INLINE ON VISIT)
                # -------------------------------
                visit.weight_kg = Decimal(randint(10, 95))
                visit.temperature_c = Decimal(str(round(36 + random() * 3, 1)))
                visit.pulse_bpm = randint(60, 120)
                visit.bp_systolic = randint(90, 160)
                visit.bp_diastolic = randint(60, 110)
                visit.resp_rate = randint(12, 30)
                visit.spo2 = randint(92, 100)
                visit.save()

                # Prescriptions
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

                # Labs
                for _lr in range(randint(0, 2)):
                    lr = LabRequest.objects.create(
                        visit=visit,
                        test=choice(tests),
                        priority=choice(["ROUTINE", "URGENT"]),
                        status="DONE",
                    )
                    LabResult.objects.create(
                        lab_request=lr,
                        result_text=choice(["Normal", "High", "Low"]),
                        performed_by=billing,
                    )

                # Invoice + payment
                inv = generate_invoice_for_visit(visit, user=billing)

                if inv.patient_amount > 0 and random() < 0.6:
                    Payment.objects.create(
                        invoice=inv,
                        amount=inv.patient_amount / 2,
                        method=choice(
                            [Payment.Method.CASH, Payment.Method.POS]
                        ),
                        reference=f"DEMO-{fake.uuid4()[:8]}",
                        received_by=billing,
                    )

        # -------------------------------------------------
        # FOLLOW-UP
        # -------------------------------------------------
        today = timezone.localdate()
        HMOFollowUp.objects.get_or_create(
            hmo_name=hmo_names[0],
            period_start=today - timedelta(days=30),
            period_end=today,
            defaults={
                "status": HMOFollowUp.Status.REMINDED,
                "next_follow_up_at": today + timedelta(days=7),
                "notes": "Demo follow-up created by seed command.",
                "owner": billing,
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. Patients created: {created_patients}"
        ))
