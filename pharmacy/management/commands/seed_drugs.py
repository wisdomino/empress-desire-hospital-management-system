from django.core.management.base import BaseCommand
from pharmacy.models import Drug

DRUGS = [
    ("Paracetamol", "500mg", "Tablet"),
    ("Ibuprofen", "400mg", "Tablet"),
    ("Amoxicillin", "500mg", "Capsule"),
    ("Amoxicillin-Clavulanate", "625mg", "Tablet"),
    ("Ciprofloxacin", "500mg", "Tablet"),
    ("Metronidazole", "400mg", "Tablet"),
    ("Artemether/Lumefantrine", "20/120mg", "Tablet"),
    ("Omeprazole", "20mg", "Capsule"),
    ("ORS", "", "Sachet"),
    ("Cetirizine", "10mg", "Tablet"),
]

class Command(BaseCommand):
    help = "Seed common drugs"

    def handle(self, *args, **options):
        created = 0
        for name, strength, dosage_form in DRUGS:
            obj, was_created = Drug.objects.get_or_create(
                name=name, strength=strength, dosage_form=dosage_form,
                defaults={"active": True}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded drugs. New created: {created}"))
