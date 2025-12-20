from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.utils import require_roles
from visits.models import Visit
from .forms import PrescriptionItemForm
from .models import PrescriptionItem

@login_required
def add_prescription(request, visit_id: int):
    require_roles(request.user, roles={"doctor", "admin"})

    visit = get_object_or_404(Visit, pk=visit_id)
    form = PrescriptionItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.visit = visit
        item.save()
    return redirect("visits:consultation", visit_id=visit.id)

@login_required
def pharmacy_queue(request):
    require_roles(request.user, roles={"pharmacy", "admin"})

    items = PrescriptionItem.objects.select_related("visit__patient", "drug").filter(
        status=PrescriptionItem.Status.PENDING
    ).order_by("created_at")

    return render(request, "pharmacy/queue.html", {"items": items})

@login_required
def mark_dispensed(request, item_id: int):
    require_roles(request.user, roles={"pharmacy", "admin"})

    item = get_object_or_404(PrescriptionItem, pk=item_id)
    item.status = PrescriptionItem.Status.DISPENSED
    item.save(update_fields=["status"])
    return redirect("pharmacy:queue")

