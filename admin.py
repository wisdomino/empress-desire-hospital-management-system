from django.contrib import admin
from .models import LabTest, LabRequest, LabResult

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "active")
    search_fields = ("name", "category")
    list_filter = ("active", "category")

@admin.register(LabRequest)
class LabRequestAdmin(admin.ModelAdmin):
    list_display = ("visit", "test", "priority", "status", "requested_at")
    search_fields = ("visit__visit_number", "test__name")
    list_filter = ("priority", "status")

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("lab_request", "performed_by", "created_at")
    search_fields = ("lab_request__visit__visit_number", "lab_request__test__name")
