from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.utils import require_roles
from billing.models import HMOClaimBatch, HMOClaimItem, Invoice, Payment

@login_required
def claim_batch_list(request):
    require_roles(request.user, roles={"billing", "admin"})
    batches = HMOClaimBatch.objects.order_by("-created_at")
    return render(request, "billing/claims/batch_list.html", {"batches": batches})


@login_required
def claim_batch_create(request):
    require_roles(request.user, roles={"billing", "admin"})

    if request.method == "POST":
        hmo_name = (request.POST.get("hmo_name") or "").strip()
        period_start = request.POST.get("period_start")
        period_end = request.POST.get("period_end")

        batch = HMOClaimBatch.objects.create(
            hmo_name=hmo_name,
            period_start=period_start,
            period_end=period_end,
            status="DRAFT",
        )
        return redirect("billing:claim_batch_detail", batch_id=batch.id)

    # quick defaults: current month
    today = timezone.localdate()
    start = today.replace(day=1)
    return render(request, "billing/claims/batch_create.html", {
        "default_start": start,
        "default_end": today,
    })


@login_required
def claim_batch_detail(request, batch_id: int):
    require_roles(request.user, roles={"billing", "admin"})
    batch = get_object_or_404(HMOClaimBatch, pk=batch_id)

    items = batch.items.select_related("invoice").order_by("-created_at")
    total_hmo = items.aggregate(total=Sum("hmo_amount"))["total"] or Decimal("0.00")

    return render(request, "billing/claims/batch_detail.html", {
        "batch": batch,
        "items": items,
        "total_hmo": total_hmo,
    })


@login_required
def claim_batch_add_invoices(request, batch_id: int):
    """
    Add eligible invoices into batch:
    - invoice has HMO amount > 0
    - invoice created within period
    - invoice hmo_name matches batch.hmo_name
    - not already in ANY claim batch item (to avoid double-claiming)
    """
    require_roles(request.user, roles={"billing", "admin"})
    batch = get_object_or_404(HMOClaimBatch, pk=batch_id)

    if request.method == "POST":
        invoice_ids = request.POST.getlist("invoice_ids")
        invoices = Invoice.objects.select_related("patient", "visit").filter(id__in=invoice_ids)

        created = 0
        for inv in invoices:
            if inv.hmo_amount <= 0:
                continue
            if inv.hmo_name != batch.hmo_name:
                continue
            # prevent duplicate claim of same invoice
            if HMOClaimItem.objects.filter(invoice=inv).exists():
                continue

            HMOClaimItem.objects.create(
                batch=batch,
                invoice=inv,
                hmo_amount=inv.hmo_amount,
                patient=f"{inv.patient.last_name} {inv.patient.first_name}",
                hospital_number=inv.patient.hospital_number,
                visit_number=(inv.visit.visit_number if inv.visit else ""),
            )
            created += 1

        return redirect("billing:claim_batch_detail", batch_id=batch.id)

    # Eligible invoice search set
    start = batch.period_start
    end = batch.period_end

    eligible = (
        Invoice.objects.select_related("patient", "visit")
        .filter(hmo_amount__gt=0, hmo_name=batch.hmo_name, created_at__date__gte=start, created_at__date__lte=end)
        .exclude(id__in=HMOClaimItem.objects.values_list("invoice_id", flat=True))
        .order_by("-created_at")
    )[:300]

    return render(request, "billing/claims/add_invoices.html", {
        "batch": batch,
        "eligible": eligible,
    })


@login_required
def claim_batch_export_csv(request, batch_id: int):
    require_roles(request.user, roles={"billing", "admin"})
    batch = get_object_or_404(HMOClaimBatch, pk=batch_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="EDH_HMO_CLAIMS_{batch.id}.csv"'

    import csv
    writer = csv.writer(response)
    writer.writerow([
        "HMO", "Period Start", "Period End",
        "Hospital No", "Patient", "Visit No", "Invoice", "HMO Amount"
    ])

    for item in batch.items.select_related("invoice").all():
        writer.writerow([
            batch.hmo_name, batch.period_start, batch.period_end,
            item.hospital_number, item.patient, item.visit_number,
            item.invoice.invoice_number, item.hmo_amount
        ])

    return response


@login_required
def claim_batch_submit(request, batch_id: int):
    require_roles(request.user, roles={"billing", "admin"})
    batch = get_object_or_404(HMOClaimBatch, pk=batch_id)
    if batch.status == "DRAFT":
        batch.status = "SUBMITTED"
        batch.save(update_fields=["status"])
    return redirect("billing:claim_batch_detail", batch_id=batch.id)


@login_required
def claim_batch_mark_paid(request, batch_id: int):
    """
    When HMO pays, post settlements against invoices as Payment(method=HMO).
    This does NOT affect patient balances; it just records HMO receivable settlement.
    """
    require_roles(request.user, roles={"billing", "admin"})
    batch = get_object_or_404(HMOClaimBatch, pk=batch_id)

    if request.method == "POST":
        reference = (request.POST.get("reference") or "").strip()

        for item in batch.items.select_related("invoice").all():
            inv = item.invoice
            if item.hmo_amount <= 0:
                continue

            # avoid double posting HMO settlement for same invoice/batch
            already = inv.payments.filter(method=Payment.Method.HMO, reference=reference).exists()
            if already:
                continue

            Payment.objects.create(
                invoice=inv,
                amount=item.hmo_amount,
                method=Payment.Method.HMO,
                reference=reference,
                received_by=request.user,
            )

        batch.status = "PAID"
        batch.save(update_fields=["status"])
        return redirect("billing:claim_batch_detail", batch_id=batch.id)

    return redirect("billing:claim_batch_detail", batch_id=batch.id)
