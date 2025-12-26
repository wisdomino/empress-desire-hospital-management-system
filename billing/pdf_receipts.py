from io import BytesIO
from decimal import Decimal

from django.http import HttpResponse, Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def _money(v) -> str:
    try:
        return f"{Decimal(v):,.2f}"
    except Exception:
        return f"{v}"


def render_receipt_pdf(*, hospital, invoice, payment) -> bytes:
    """
    Render a simple receipt PDF similar to your HTML template using ReportLab.
    Returns PDF bytes.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    left = 18 * mm
    right = width - 18 * mm
    y = height - 20 * mm

    # ---- Header (Hospital) ----
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, getattr(hospital, "name", "Hospital"))
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    addr = getattr(hospital, "address", "")
    phone = getattr(hospital, "phone", "")
    email = getattr(hospital, "email", "")
    if addr:
        c.drawCentredString(width / 2, y, addr)
        y -= 4.5 * mm
    c.drawCentredString(width / 2, y, f"{phone} • {email}".strip(" •"))
    y -= 8 * mm

    # dashed separator
    c.setDash(3, 2)
    c.line(left, y, right, y)
    c.setDash()  # reset
    y -= 10 * mm

    # ---- Receipt Box ----
    box_top = y
    box_left = left
    box_right = right
    box_width = box_right - box_left
    box_height = 92 * mm
    box_bottom = box_top - box_height

    # Rounded-ish rectangle (ReportLab doesn't do true border-radius simply; keep clean)
    c.roundRect(box_left, box_bottom, box_width, box_height, 8, stroke=1, fill=0)

    y = box_top - 10 * mm

    # Title row
    c.setFont("Helvetica-Bold", 11)
    c.drawString(box_left + 8 * mm, y, "RECEIPT")

    paid_at = getattr(payment, "paid_at", None)
    paid_at_str = paid_at.strftime("%b %d, %Y %H:%M") if paid_at else ""
    c.setFont("Helvetica", 9)
    c.drawRightString(box_right - 8 * mm, y + 1, paid_at_str)
    y -= 9 * mm

    def row(label, value, bold=False):
        nonlocal y
        c.setFont("Helvetica", 9)
        c.setFillGray(0.35)
        c.drawString(box_left + 8 * mm, y, label)
        c.setFillGray(0)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
        c.drawRightString(box_right - 8 * mm, y, value)
        y -= 6.2 * mm

    # Invoice / Patient rows
    row("Invoice", getattr(invoice, "invoice_number", ""), bold=True)

    patient = getattr(invoice, "patient", None)
    patient_name = ""
    hosp_no = ""
    if patient:
        patient_name = f"{getattr(patient, 'last_name', '')} {getattr(patient, 'first_name', '')}".strip()
        hosp_no = getattr(patient, "hospital_number", "")

    row("Patient", patient_name, bold=True)
    row("Hospital No", hosp_no, bold=True)

    # divider
    y -= 2 * mm
    c.setDash(2, 2)
    c.line(box_left + 8 * mm, y, box_right - 8 * mm, y)
    c.setDash()
    y -= 8 * mm

    # Amount paid big
    c.setFont("Helvetica", 9)
    c.setFillGray(0.35)
    c.drawString(box_left + 8 * mm, y, "Amount Paid")
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 15)
    c.drawRightString(box_right - 8 * mm, y - 1, f"₦{_money(getattr(payment, 'amount', 0))}")
    y -= 9 * mm

    # Method / Reference
    method = getattr(payment, "get_method_display", None)
    method_str = method() if callable(method) else getattr(payment, "method", "")
    ref = getattr(payment, "reference", "") or "—"

    row("Method", str(method_str), bold=True)
    row("Reference", str(ref), bold=False)

    # divider
    y -= 2 * mm
    c.setDash(2, 2)
    c.line(box_left + 8 * mm, y, box_right - 8 * mm, y)
    c.setDash()
    y -= 7 * mm

    # Summary values from invoice
    row("Patient Share", f"₦{_money(getattr(invoice, 'patient_amount', 0))}")
    row("Total Paid", f"₦{_money(getattr(invoice, 'amount_paid', 0))}")
    row("Balance", f"₦{_money(getattr(invoice, 'balance', 0))}", bold=True)

    # Footer
    y = box_bottom - 10 * mm
    c.setFont("Helvetica", 8)
    c.setFillGray(0.4)
    generated_at = timezone.now()
    c.drawCentredString(width / 2, y, f"Generated: {generated_at.strftime('%b %d, %Y %H:%M')} • Thank you.")
    c.setFillGray(0)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
