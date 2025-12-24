from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.utils import require_roles
from patients.models import Patient
from .forms import VisitStartForm, VitalsForm
from .models import Visit
from .forms import ConsultationForm
from pharmacy.forms import PrescriptionItemForm
from lab.forms import LabRequestForm
from django.utils import timezone
from billing.services import generate_invoice_for_visit

@login_required
def start_visit(request, patient_id: int):
    require_roles(request.user, roles={"frontdesk", "nurse", "admin"})

    patient = get_object_or_404(Patient, pk=patient_id)

    form = VisitStartForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        visit: Visit = form.save(commit=False)
        visit.patient = patient
        visit.status = Visit.Status.OPEN
        visit.save()
        return redirect("visits:vitals_update", visit_id=visit.id)

    return render(request, "visits/visit_start.html", {"patient": patient, "form": form})


@login_required
def vitals_update(request, visit_id: int):
    require_roles(request.user, roles={"frontdesk", "nurse", "admin"})

    visit = get_object_or_404(Visit, pk=visit_id)

    form = VitalsForm(request.POST or None, instance=visit)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        # once vitals are captured, move to doctor queue
        updated.status = Visit.Status.WAITING_DOCTOR
        updated.save()
        return redirect("visits:queue")

    return render(request, "visits/vitals_form.html", {"visit": visit, "form": form})


@login_required
def queue(request):
    require_roles(request.user, roles={"doctor", "admin", "frontdesk", "nurse"})

    visits = Visit.objects.select_related("patient").filter(
        status__in=[Visit.Status.OPEN, Visit.Status.WAITING_DOCTOR, Visit.Status.IN_CONSULT]
    ).order_by("created_at")

    return render(request, "visits/queue.html", {"visits": visits})


@login_required
def visit_detail(request, visit_id: int):
    # doctors + frontdesk/nurse can view visit summary
    require_roles(request.user, roles={"doctor", "admin", "frontdesk", "nurse"})

    visit = get_object_or_404(Visit.objects.select_related("patient"), pk=visit_id)
    return render(request, "visits/visit_detail.html", {"visit": visit})


@login_required
def doctor_take_case(request, visit_id: int):
    require_roles(request.user, roles={"doctor", "admin"})

    visit = get_object_or_404(Visit, pk=visit_id)
    if visit.status in [Visit.Status.OPEN, Visit.Status.WAITING_DOCTOR]:
        visit.status = Visit.Status.IN_CONSULT
        if request.user.role == "doctor":
            visit.doctor = request.user
        visit.save(update_fields=["status", "doctor", "updated_at"])
    return redirect("visits:visit_detail", visit_id=visit.id)

@login_required
def consultation(request, visit_id: int):
    require_roles(request.user, roles={"doctor", "admin"})

    visit = get_object_or_404(Visit.objects.select_related("patient"), pk=visit_id)

    if visit.status in [Visit.Status.OPEN, Visit.Status.WAITING_DOCTOR]:
        visit.status = Visit.Status.IN_CONSULT
        if request.user.role == "doctor":
            visit.doctor = request.user
        visit.save(update_fields=["status", "doctor", "updated_at"])

    form = ConsultationForm(request.POST or None, instance=visit)

    # IMPORTANT: these are the forms for the right-side panels
    prescription_form = PrescriptionItemForm()
    lab_request_form = LabRequestForm()

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("visits:consultation", visit_id=visit.id)

    return render(request, "visits/consultation.html", {
        "visit": visit,
        "form": form,
        "prescription_form": prescription_form,
        "lab_request_form": lab_request_form,
        "prescriptions": visit.prescriptions.select_related("drug").order_by("-created_at"),
        "lab_requests": visit.lab_requests.select_related("test").order_by("-requested_at"),
    })


@login_required
def close_visit(request, visit_id: int):
    require_roles(request.user, roles={"doctor", "admin"})
    visit = get_object_or_404(Visit, pk=visit_id)

    # Mark closed
    visit.status = Visit.Status.CLOSED
    visit.closed_at = timezone.now()
    visit.save(update_fields=["status", "closed_at", "updated_at"])

    # ✅ Idempotent invoice creation:
    # If invoice already exists for this visit, reuse it.
    if hasattr(visit, "invoice") and visit.invoice is not None:
        return redirect("billing:invoice_detail", visit.invoice.id)

    # Otherwise generate once
    generate_invoice_for_visit(visit, user=request.user)

    # Reload visit to ensure invoice relation is available
    visit = Visit.objects.select_related("invoice").get(pk=visit.id)

    # Safety fallback (should not happen after model fix)
    if not getattr(visit, "invoice", None):
        return redirect("visits:visit_detail", visit_id=visit.id)

    return redirect("billing:invoice_detail", visit.invoice.id)
