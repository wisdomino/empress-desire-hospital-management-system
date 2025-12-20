from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.utils import require_roles
from visits.models import Visit
from .forms import LabRequestForm, LabResultForm
from .models import LabRequest, LabResult

@login_required
def add_lab_request(request, visit_id: int):
    require_roles(request.user, roles={"doctor", "admin"})

    visit = get_object_or_404(Visit, pk=visit_id)
    form = LabRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        lr = form.save(commit=False)
        lr.visit = visit
        lr.save()
    return redirect("visits:consultation", visit_id=visit.id)

@login_required
def lab_queue(request):
    require_roles(request.user, roles={"lab", "admin"})

    requests = LabRequest.objects.select_related("visit__patient", "test").filter(
        status__in=[LabRequest.Status.REQUESTED, LabRequest.Status.SAMPLE_COLLECTED]
    ).order_by("requested_at")

    return render(request, "lab/queue.html", {"requests": requests})

@login_required
def upload_result(request, lab_request_id: int):
    require_roles(request.user, roles={"lab", "admin"})

    lab_request = get_object_or_404(LabRequest.objects.select_related("visit__patient", "test"), pk=lab_request_id)

    result_obj = getattr(lab_request, "result", None)
    form = LabResultForm(request.POST or None, instance=result_obj)

    if request.method == "POST" and form.is_valid():
        r = form.save(commit=False)
        r.lab_request = lab_request
        r.performed_by = request.user
        r.save()
        lab_request.status = LabRequest.Status.RESULT_READY
        lab_request.save(update_fields=["status"])
        return redirect("lab:queue")

    return render(request, "lab/upload_result.html", {"lab_request": lab_request, "form": form})
