import csv
from django.http import HttpResponse
from .models import HMOClaimBatch

def export_claim_batch_csv(batch_id):
    batch = HMOClaimBatch.objects.prefetch_related("items").get(pk=batch_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="EDH_HMO_CLAIMS_{batch.id}.csv"'

    writer = csv.writer(response)
    writer.writerow(["HMO", "Period Start", "Period End", "Hospital No", "Patient", "Visit No", "Invoice", "HMO Amount"])

    for item in batch.items.all():
        writer.writerow([
            batch.hmo_name, batch.period_start, batch.period_end,
            item.hospital_number, item.patient, item.visit_number,
            item.invoice.invoice_number, item.hmo_amount
        ])

    return response
