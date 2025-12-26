from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import Invoice, Payment, HMOClaimBatch
from .pdf_receipts import render_receipt_pdf
from .pdf_hmo_reminder import build_hmo_reminder_pdf


# ------------------------------------------------------------------
# Hospital meta fallback
# ------------------------------------------------------------------
HOSPITAL_META = {
    "name": "EMPRESS DESIRE HOSPITAL",
    "address": "Port Harcourt, Rivers State, Nigeria",
    "phone": "+2348067086554",
    "email": "info@empressdesirehospital.com",
}


def _get_hospital():
    hospital = HospitalProfile.objects.first()
    if hospital:
        return hospital
    return type(
        "Hospital",
        (),
        HOSPITAL_META
    )()


# ------------------------------------------------------------------
# INVOICE PDF
# ------------------------------------------------------------------
@login_required
def invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.select_related("patient", "visit")
        .prefetch_related("lines", "payments"),
        pk=invoice_id,
    )

    from .pdf_invoices import render_invoice_pdf  # if you later move it
    pdf_bytes = render_invoice_pdf(invoice=invoice, hospital=_get_hospital())

    filename = f"{invoice.invoice_number}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


# ------------------------------------------------------------------
# RECEIPT PDF
# ------------------------------------------------------------------
@login_required
def receipt_pdf(request, invoice_id, payment_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    payment = get_object_or_404(Payment, id=payment_id, invoice=invoice)

    pdf_bytes = render_receipt_pdf(
        hospital=_get_hospital(),
        invoice=invoice,
        payment=payment,
    )

    filename = f"Receipt_{invoice.invoice_number}_P{payment.id}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


# ------------------------------------------------------------------
# CLAIM COVER SHEET PDF
# ------------------------------------------------------------------
@login_required
def claim_cover_pdf(request, batch_id):
    batch = get_object_or_404(
        HMOClaimBatch.objects.prefetch_related("items__invoice"),
        pk=batch_id,
    )

    total_hmo = batch.items.aggregate(
        total=Sum("hmo_amount")
    )["total"] or 0

    from .pdf_claims import render_claim_cover_pdf  # optional split
    pdf_bytes = render_claim_cover_pdf(
        hospital=_get_hospital(),
        batch=batch,
        items=batch.items.select_related("invoice").all(),
        total_hmo=total_hmo,
    )

    filename = f"EDH_HMO_CLAIM_COVER_{batch.id}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


# ------------------------------------------------------------------
# HMO REMINDER LETTER PDF  ✅ FIXES YOUR ERROR
# ------------------------------------------------------------------
@login_required
def hmo_reminder_letter_pdf(request, hmo_name):
    hospital = _get_hospital()

    # TODO: replace with real aging query
    rows = []              # [{"inv": invoice, "days": int, "outstanding": Decimal}]
    total_outstanding = 0  # Decimal

    pdf_bytes = build_hmo_reminder_pdf(
        hospital=hospital,
        hmo_name=hmo_name,
        rows=rows,
        total_outstanding=total_outstanding,
        generated_at=timezone.now(),
    )

    filename = f"HMO_Reminder_{hmo_name}".replace(" ", "_") + ".pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


# ------------------------------------------------------------------
# HMO DISPUTE SHEET PDF  ✅ THIS WAS MISSING / BROKEN
# ------------------------------------------------------------------
@login_required
def hmo_dispute_sheet_pdf(request, hmo_name):
    hospital = _get_hospital()

    # TODO: load disputed invoices properly
    disputed_rows = []

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, "HMO DISPUTE SHEET")

    c.setFont("Helvetica", 10)
    c.drawString(50, 780, f"HMO: {hmo_name}")
    c.drawString(50, 765, f"Generated: {timezone.now().strftime('%b %d, %Y %H:%M')}")

    y = 730
    if not disputed_rows:
        c.drawString(50, y, "No disputed invoices found.")
    else:
        for r in disputed_rows:
            c.drawString(50, y, str(r))
            y -= 15

    c.showPage()
    c.save()

    pdf_bytes = buf.getvalue()
    buf.close()

    filename = f"HMO_Disputes_{hmo_name}".replace(" ", "_") + ".pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp
