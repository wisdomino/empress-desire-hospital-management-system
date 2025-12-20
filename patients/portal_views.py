from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Patient
from visits.models import Visit
from .portal_utils import patient_only

@login_required
def patient_dashboard(request):
    patient_only(request.user)

    patient = get_object_or_404(Patient, user=request.user)
    visits = patient.visits.select_related("doctor").order_by("-created_at")

    return render(request, "patients/portal/dashboard.html", {
        "patient": patient,
        "visits": visits,
    })


@login_required
def patient_visit_detail(request, visit_id):
    patient_only(request.user)

    visit = get_object_or_404(
        Visit.objects.select_related("patient"),
        id=visit_id,
        patient__user=request.user
    )

    return render(request, "patients/portal/visit_detail.html", {
        "visit": visit
    })
