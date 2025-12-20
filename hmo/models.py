from django.db import models

class HMO(models.Model):
    name = models.CharField(max_length=120, unique=True)
    contact_person = models.CharField(max_length=120, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
