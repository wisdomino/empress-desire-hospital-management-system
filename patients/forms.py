from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name","last_name","other_names",
            "gender","date_of_birth",
            "phone","email","address",
            "passport_photo",
            "is_hmo","hmo","hmo_id_number",
            "next_of_kin_name","next_of_kin_phone",
            "blood_group","allergies",
        ]
