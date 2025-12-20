from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Visit

@receiver(post_save, sender=Visit)
def set_visit_number(sender, instance: Visit, created, **kwargs):
    if created and not instance.visit_number:
        instance.visit_number = f"EDH-V-{instance.id:06d}"
        instance.save(update_fields=["visit_number"])
