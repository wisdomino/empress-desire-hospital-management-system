from django import forms
from .models import PrescriptionItem, Drug

class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ["drug", "dose", "frequency", "duration", "instructions"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qs = Drug.objects.all()
        # prefer is_active if it exists, else active if it exists
        field_names = {f.name for f in Drug._meta.fields}
        if "is_active" in field_names:
            qs = Drug.objects.filter(is_active=True)
        elif "active" in field_names:
            qs = Drug.objects.filter(active=True)

        self.fields["drug"].queryset = qs.order_by("name")
