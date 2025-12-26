from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice

@receiver(post_save, sender=Invoice)
def set_invoice_number(sender, instance: Invoice, created, **kwargs):
    if created and not instance.invoice_number:
        instance.invoice_number = f"EDH-INV-{instance.id:06d}"
        instance.save(update_fields=["invoice_number"])
