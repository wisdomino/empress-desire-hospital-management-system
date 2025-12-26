from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from accounts.utils import require_roles
from .models import Payment, Invoice
from django.shortcuts import render
from .models import HMOFollowUp

@login_required
def revenue_dashboard(request):
    require_roles(request.user, roles={"admin", "billing"})

    today = timezone.localdate()
    start = today.replace(day=1)  # month-to-date



    followups_due = (
        HMOFollowUp.objects
        .filter(next_follow_up_at__lte=today)
        .exclude(status="SETTLED")
        .count()
    )

    # Collections
    payments_today = Payment.objects.filter(paid_at__date=today).aggregate(total=Sum("amount"))["total"] or 0
    payments_mtd = Payment.objects.filter(paid_at__date__gte=start, paid_at__date__lte=today).aggregate(total=Sum("amount"))["total"] or 0

    # Outstanding + HMO receivables
    outstanding = Invoice.objects.aggregate(total=Sum("balance"))["total"] or 0
    hmo_receivables = Invoice.objects.aggregate(total=Sum("hmo_amount"))["total"] or 0

    # Trend (last 30 days)
    last30 = today - timezone.timedelta(days=29)
    trend_qs = (
        Payment.objects.filter(paid_at__date__gte=last30)
        .annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )

    # Method breakdown
    by_method = (
        Payment.objects.filter(paid_at__date__gte=last30)
        .values("method")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    return render(request, "billing/dashboard.html", {
        "payments_today": payments_today,
        "payments_mtd": payments_mtd,
        "outstanding": outstanding,
        "hmo_receivables": hmo_receivables,
        "trend": list(trend_qs),
        "by_method": list(by_method),
        "followups_due": followups_due,
    })

