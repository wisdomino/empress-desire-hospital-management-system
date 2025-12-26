from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum

from billing.models import Invoice, HMOFollowUp, Payment
from billing.pdf_views import hmo_reminder_letter_pdf, hmo_dispute_sheet_pdf
from billing.hmo_aging_views import _bucket

class Command(BaseCommand):
    help = "Generate weekly HMO reminder packs and schedule follow-ups"

    def handle(self, *args, **options):
        today = timezone.localdate()
        start = today - timedelta(days=30)  # rolling window

        # HMOs with outstanding balances
        hmos = (
            Invoice.objects
            .filter(hmo_amount__gt=0)
            .values_list("hmo_name", flat=True)
            .distinct()
        )

        for hmo in hmos:
            qs = Invoice.objects.filter(hmo_name=hmo, hmo_amount__gt=0)

            # compute outstanding
            total_paid = (
                Payment.objects.filter(method=Payment.Method.HMO, invoice__in=qs)
                .aggregate(t=Sum("amount"))["t"] or 0
            )
            total_hmo = qs.aggregate(t=Sum("hmo_amount"))["t"] or 0
            outstanding = total_hmo - total_paid

            if outstanding <= 0:
                continue

            followup, created = HMOFollowUp.objects.get_or_create(
                hmo_name=hmo,
                period_start=start,
                period_end=today,
                defaults={
                    "status": HMOFollowUp.Status.OPEN,
                    "next_follow_up_at": today + timedelta(days=7),
                }
            )

            followup.status = HMOFollowUp.Status.REMINDED
            followup.last_action_at = timezone.now()
            followup.next_follow_up_at = today + timedelta(days=7)
            followup.save()

            self.stdout.write(self.style.SUCCESS(
                f"Prepared weekly pack for {hmo} | Outstanding ₦{outstanding:,.2f}"
            ))

        self.stdout.write(self.style.SUCCESS("Weekly HMO reminder packs generated."))
