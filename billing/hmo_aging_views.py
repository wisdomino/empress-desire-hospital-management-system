from decimal import Decimal
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render
from django.utils import timezone

from accounts.utils import require_roles
from billing.models import Invoice, Payment


def _bucket(days: int) -> str:
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


@login_required
def hmo_aging_dashboard(request):
    require_roles(request.user, roles={"admin", "billing"})

    today: date = timezone.localdate()

    # Only invoices with HMO component
    invoices = (
        Invoice.objects
        .select_related("patient", "visit")
        .filter(hmo_amount__gt=0)
        .order_by("-created_at")
    )

    # Pre-aggregate HMO payments per invoice (method=HMO)
    hmo_paid_map = dict(
        Payment.objects
        .filter(method=Payment.Method.HMO)
        .values("invoice_id")
        .annotate(total=Sum("amount"))
        .values_list("invoice_id", "total")
    )

    # Build aging by HMO
    by_hmo = {}  # {hmo_name: {"0-30": x, "31-60": y, ... , "total": t}}
    grand = {"0-30": Decimal("0.00"), "31-60": Decimal("0.00"), "61-90": Decimal("0.00"), "90+": Decimal("0.00"), "total": Decimal("0.00")}

    # Optional drill list (top outstanding invoices)
    rows = []

    for inv in invoices:
        hmo_name = (inv.hmo_name or "").strip() or "UNKNOWN HMO"
        paid = Decimal(hmo_paid_map.get(inv.id) or 0)
        outstanding = (Decimal(inv.hmo_amount) - paid).quantize(Decimal("0.01"))

        if outstanding <= 0:
            continue

        days = (today - inv.created_at.date()).days
        b = _bucket(days)

        if hmo_name not in by_hmo:
            by_hmo[hmo_name] = {"0-30": Decimal("0.00"), "31-60": Decimal("0.00"), "61-90": Decimal("0.00"), "90+": Decimal("0.00"), "total": Decimal("0.00")}

        by_hmo[hmo_name][b] += outstanding
        by_hmo[hmo_name]["total"] += outstanding

        grand[b] += outstanding
        grand["total"] += outstanding

        rows.append({
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "hospital_number": inv.patient.hospital_number,
            "patient": f"{inv.patient.last_name} {inv.patient.first_name}",
            "hmo_name": hmo_name,
            "days": days,
            "bucket": b,
            "outstanding": outstanding,
            "created_at": inv.created_at,
        })

    # Sort HMOs by total outstanding desc
    hmo_table = [
        {"hmo_name": name, **vals}
        for name, vals in by_hmo.items()
    ]
    hmo_table.sort(key=lambda x: x["total"], reverse=True)

    # Sort invoice drill list by outstanding desc, take top 50
    rows.sort(key=lambda x: x["outstanding"], reverse=True)
    top_invoices = rows[:50]

    # Chart data
    chart_labels = [x["hmo_name"] for x in hmo_table[:10]]  # top 10 HMOs
    chart_totals = [float(x["total"]) for x in hmo_table[:10]]

    bucket_labels = ["0-30", "31-60", "61-90", "90+"]
    bucket_totals = [float(grand[b]) for b in bucket_labels]

    return render(request, "billing/hmo_aging_dashboard.html", {
        "hmo_table": hmo_table,
        "grand": grand,
        "top_invoices": top_invoices,
        "chart_labels": chart_labels,
        "chart_totals": chart_totals,
        "bucket_labels": bucket_labels,
        "bucket_totals": bucket_totals,
        "today": today,
    })
