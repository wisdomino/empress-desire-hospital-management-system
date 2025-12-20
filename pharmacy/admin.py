from django.contrib import admin
from .models import Drug, PrescriptionItem


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ("name", "strength", "dosage_form", "price", "is_active")
    search_fields = ("name",)
    list_filter = ("dosage_form", "is_active")

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ("visit", "drug", "status", "created_at")
    search_fields = ("visit__visit_number", "drug__name")
    list_filter = ("status",)