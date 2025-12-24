from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.utils import require_roles
from .models import Invoice, Payment

@login_required
def invoice_list(request):
    require_roles(request.user, roles={"billing", "admin", "frontdesk"})
    q = (request.GET.get("q") or "").strip()

    qs = Invoice.objects.select_related("patient", "visit").order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(invoice_number__icontains=q) |
            Q(patient__hospital_number__icontains=q) |
            Q(patient__first_name__icontains=q) |
            Q(patient__last_name__icontains=q)
        )

    return render(request, "billing/invoice_list.html", {"invoices": qs[:200], "q": q})


@login_required
def invoice_detail(request, invoice_id):
    require_roles(request.user, roles={"billing", "admin", "frontdesk"})
    invoice = get_object_or_404(Invoice.objects.select_related("patient", "visit"), pk=invoice_id)
    return render(request, "billing/invoice_detail.html", {"invoice": invoice})


@login_required
def add_payment(request, invoice_id):
    require_roles(request.user, roles={"billing", "admin"})
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount") or "0")
        method = request.POST.get("method")
        reference = (request.POST.get("reference") or "").strip()

        Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method=method,
            reference=reference,
            received_by=request.user,
        )

        # recompute invoice figures
        from billing.services import generate_invoice_for_visit
        if invoice.visit:
            generate_invoice_for_visit(invoice.visit, user=request.user)
        else:
            # fallback if not tied to visit
            invoice.amount_paid = sum((p.amount for p in invoice.payments.all()), Decimal("0.00"))
            invoice.balance = (invoice.patient_amount - invoice.amount_paid).quantize(Decimal("0.01"))
            invoice.save()

        return redirect("billing:invoice_detail", invoice_id=invoice.id)

    return redirect("billing:invoice_detail", invoice_id=invoice.id)
