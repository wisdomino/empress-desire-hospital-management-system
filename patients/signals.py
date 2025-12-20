from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Patient

@receiver(post_save, sender=Patient)
def set_hospital_number(sender, instance: Patient, created, **kwargs):
    if created and not instance.hospital_number:
        instance.hospital_number = f"EDH-{instance.id:06d}"
        instance.save(update_fields=["hospital_number"])
