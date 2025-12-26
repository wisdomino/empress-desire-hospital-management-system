from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

from .models import HMOFollowUp


@login_required
def followups_list(request):
    today = timezone.localdate()
    followups = (
        HMOFollowUp.objects
        .filter(next_follow_up_at__lte=today)
        .exclude(status="SETTLED")
        .order_by("next_follow_up_at", "hmo_name")
    )
    return render(request, "billing/followups_list.html", {
        "today": today,
        "followups": followups,
    })


@login_required
def followup_update(request, followup_id: int):
    f = get_object_or_404(HMOFollowUp, pk=followup_id)

    if request.method == "POST":
        # basic fields (safe + simple)
        f.status = request.POST.get("status", f.status)
        notes = request.POST.get("notes", "")
        f.notes = notes

        next_date = request.POST.get("next_follow_up_at")
        if next_date:
            # YYYY-MM-DD from <input type="date">
            f.next_follow_up_at = next_date

        f.last_action_at = timezone.now()
        f.save()

        messages.success(request, "Follow-up updated.")
        return redirect("billing:followups_list")

    return render(request, "billing/followup_update.html", {"f": f})
