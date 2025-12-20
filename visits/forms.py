from django import forms
from .models import Visit

class VisitStartForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ["visit_type"]

class VitalsForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = [
            "height_cm","weight_kg",
            "bp_systolic","bp_diastolic",
            "temperature_c","pulse_bpm","resp_rate","spo2",
            "triage_note",
        ]
        widgets = {
            "triage_note": forms.Textarea(attrs={"rows": 3}),
        }
class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = [
            "chief_complaint",
            "history_of_present_illness",
            "examination",
            "diagnosis_primary",
            "diagnosis_secondary",
            "treatment_plan",
            "doctor_notes",
        ]
        widgets = {
            "history_of_present_illness": forms.Textarea(attrs={"rows": 4}),
            "examination": forms.Textarea(attrs={"rows": 4}),
            "treatment_plan": forms.Textarea(attrs={"rows": 3}),
            "doctor_notes": forms.Textarea(attrs={"rows": 3}),
        }