from django.core.management.base import BaseCommand
from lab.models import LabTest

TESTS = [
    ("Haematology", "Full Blood Count (FBC)"),
    ("Haematology", "ESR"),
    ("Parasitology", "Malaria Parasite (MP)"),
    ("Microbiology", "Widal Test"),
    ("Microbiology", "Urine M/C/S"),
    ("Microbiology", "Stool M/C/S"),
    ("Urinalysis", "Urinalysis"),
    ("Chemistry", "Fasting Blood Sugar (FBS)"),
    ("Chemistry", "Random Blood Sugar (RBS)"),
    ("Chemistry", "Urea, Electrolytes & Creatinine (UEC)"),
    ("Chemistry", "Liver Function Test (LFT)"),
    ("Chemistry", "Lipid Profile"),
    ("Serology", "HIV 1&2"),
    ("Serology", "HBsAg"),
    ("Serology", "HCV"),
    ("Immunology", "Pregnancy Test (UPT)"),
    ("Blood Bank", "Blood Grouping"),
    ("Blood Bank", "Genotype"),
]

class Command(BaseCommand):
    help = "Seed standard lab tests"

    def handle(self, *args, **options):
        created = 0
        for category, name in TESTS:
            obj, was_created = LabTest.objects.get_or_create(name=name, defaults={"category": category, "active": True})
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded lab tests. New created: {created}"))
