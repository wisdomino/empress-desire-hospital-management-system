from django import forms
from .models import LabRequest, LabTest, LabResult

class LabRequestForm(forms.ModelForm):
    class Meta:
        model = LabRequest
        fields = ["test", "priority"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If LabTest has is_active, use it; else fall back to all()
        qs = LabTest.objects.all()
        if any(f.name == "is_active" for f in LabTest._meta.fields):
            qs = LabTest.objects.filter(is_active=True)

        self.fields["test"].queryset = qs.order_by("category", "name")


class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = ["result_text", "remarks"]
        widgets = {"result_text": forms.Textarea(attrs={"rows": 5})}
