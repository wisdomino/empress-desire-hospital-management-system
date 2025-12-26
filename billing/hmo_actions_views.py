from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.utils import require_roles
from billing.models import Invoice, Payment, HMOClaimBatch, HMOClaimItem


@login_required
def mark_invoice_disputed(request, invoice_id: int):
    require_roles(request.user, roles={"billing", "admin"})
    inv = get_object_or_404(Invoice, pk=invoice_id)

    if request.method == "POST":
        inv.hmo_state = Invoice.HMOState.DISPUTED
        inv.hmo_dispute_reason = (request.POST.get("reason") or "").strip()
        inv.hmo_dispute_amount = Decimal(request.POST.get("amount") or "0")
        inv.save(update_fields=["hmo_state", "hmo_dispute_reason", "hmo_dispute_amount"])
        return redirect("billing:hmo_aging")

    return render(request, "billing/hmo_actions/mark_disputed.html", {"invoice": inv})


@login_required
def clear_invoice_dispute(request, invoice_id: int):
    require_roles(request.user, roles={"billing", "admin"})
    inv = get_object_or_404(Invoice, pk=invoice_id)

    inv.hmo_state = Invoice.HMOState.OK
    inv.hmo_dispute_reason = ""
    inv.hmo_dispute_amount = 0
    inv.save(update_fields=["hmo_state", "hmo_dispute_reason", "hmo_dispute_amount"])
    return redirect("billing:hmo_aging")


@login_required
def flag_claim_item_disputed(request, item_id: int):
    require_roles(request.user, roles={"billing", "admin"})
    item = get_object_or_404(HMOClaimItem.objects.select_related("invoice", "batch"), pk=item_id)

    if request.method == "POST":
        item.disputed = True
        item.dispute_reason = (request.POST.get("reason") or "").strip()
        item.disputed_at = timezone.now()
        item.save(update_fields=["disputed", "dispute_reason", "disputed_at"])
        # also mark invoice state
        inv = item.invoice
        inv.hmo_state = Invoice.HMOState.DISPUTED
        inv.hmo_dispute_reason = item.dispute_reason
        inv.hmo_dispute_amount = item.hmo_amount
        inv.save(update_fields=["hmo_state", "hmo_dispute_reason", "hmo_dispute_amount"])
        return redirect("billing:claim_batch_detail", batch_id=item.batch.id)

    return render(request, "billing/hmo_actions/flag_item_disputed.html", {"item": item})


@login_required
def mark_hmo_reminded(request):
    """
    Used after generating reminder letter PDF.
    Marks all outstanding invoices for that HMO as reminded now.
    """
    require_roles(request.user, roles={"billing", "admin"})
    hmo_name = (request.GET.get("hmo") or "").strip()
    if not hmo_name:
        return redirect("billing:hmo_aging")

    now = timezone.now()
    Invoice.objects.filter(hmo_amount__gt=0, hmo_name=hmo_name).update(hmo_last_reminded_at=now)
    return redirect("billing:hmo_aging")
