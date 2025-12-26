from decimal import Decimal
from billing.models import Invoice, InvoiceLine
from billing.utils import split_amount
from pharmacy.models import PrescriptionItem

CONSULTATION_FEE = Decimal("5000.00")  # adjust for EDH

def generate_invoice_for_visit(visit, user=None):
    patient = visit.patient

    invoice, created = Invoice.objects.get_or_create(
        visit=visit,
        defaults={"patient": patient, "created_by": user}
    )

    # Clear existing lines (safe rebuild)
    invoice.lines.all().delete()

    # 1) Consultation
    ps, hs = split_amount(CONSULTATION_FEE, patient.is_hmo)
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type=InvoiceLine.LineType.CONSULTATION,
        description="Consultation Fee",
        qty=1,
        unit_price=CONSULTATION_FEE,
        patient_share=ps,
        hmo_share=hs,
    )

        

    # 3) Drugs prescribed
    for rx in visit.prescriptions.select_related("drug").all():
        price = Decimal(rx.drug.price or 0)
        ps, hs = split_amount(price, patient.is_hmo)
        InvoiceLine.objects.create(
            invoice=invoice,
            line_type=InvoiceLine.LineType.DRUG,
            description=f"Drug: {rx.drug}",
            qty=1,
            unit_price=price,
            patient_share=ps,
            hmo_share=hs,
        )

    # Totals
    total = sum((l.line_total for l in invoice.lines.all()), Decimal("0.00"))
    patient_amount = sum((l.patient_share for l in invoice.lines.all()), Decimal("0.00"))
    hmo_amount = sum((l.hmo_share for l in invoice.lines.all()), Decimal("0.00"))
    invoice.hmo_name = patient.hmo.name if patient.is_hmo and patient.hmo else ""

    invoice.total_amount = total
    invoice.patient_amount = patient_amount
    invoice.hmo_amount = hmo_amount
    invoice.amount_paid = sum((p.amount for p in invoice.payments.all()), Decimal("0.00"))
    invoice.balance = (invoice.patient_amount - invoice.amount_paid).quantize(Decimal("0.01"))

    if invoice.balance <= 0:
        invoice.status = Invoice.Status.PAID
    elif invoice.amount_paid > 0:
        invoice.status = Invoice.Status.PARTIAL
    else:
        invoice.status = Invoice.Status.UNPAID

    invoice.save()
    return invoice
