from io import BytesIO
from decimal import Decimal
from django.utils import timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def _money(v) -> str:
    try:
        return f"{Decimal(v):,.2f}"
    except Exception:
        return f"{v}"


def build_hmo_reminder_pdf(*, hospital, hmo_name: str, rows: list, total_outstanding, generated_at=None) -> bytes:
    if generated_at is None:
        generated_at = timezone.now()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 13

    brand = ParagraphStyle("brand", parent=normal, fontName="Helvetica-Bold", fontSize=14, leading=16)
    muted = ParagraphStyle("muted", parent=normal, textColor=colors.HexColor("#555555"), fontSize=9.5, leading=12)

    story = []
    story.append(Paragraph(getattr(hospital, "name", "Hospital"), brand))
    if getattr(hospital, "address", ""):
        story.append(Paragraph(getattr(hospital, "address", ""), muted))
    line3 = " • ".join([x for x in [getattr(hospital, "phone", ""), getattr(hospital, "email", "")] if x])
    if line3:
        story.append(Paragraph(line3, muted))
    story.append(Spacer(1, 10))

    # Header box text
    story.append(Paragraph("<b>REMINDER: OUTSTANDING HMO RECEIVABLES</b>", normal))
    story.append(Paragraph(f'<font color="#555555">HMO: <b>{hmo_name}</b></font>', normal))
    story.append(Paragraph(f'<font color="#555555">Generated: {generated_at.strftime("%b %d, %Y %H:%M")}</font>', normal))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Kindly find below outstanding amounts due to {getattr(hospital, 'name', 'the hospital')}. "
        "We request settlement within 7 days or advise if any invoice is under query so we can resolve promptly.",
        normal
    ))
    story.append(Spacer(1, 10))

    # Table
    data = [["Invoice", "Hospital No", "Patient", "Days", "Outstanding (₦)"]]
    for r in rows:
        inv = r.get("inv")
        patient = getattr(inv, "patient", None)

        invoice_no = getattr(inv, "invoice_number", "")
        hosp_no = getattr(patient, "hospital_number", "") if patient else ""
        patient_name = f"{getattr(patient, 'last_name', '')} {getattr(patient, 'first_name', '')}".strip() if patient else ""

        data.append([
            invoice_no,
            hosp_no,
            patient_name,
            str(r.get("days", "")),
            _money(r.get("outstanding", 0)),
        ])

    tbl = Table(data, colWidths=[34*mm, 28*mm, 58*mm, 14*mm, 32*mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F6F7FB")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#E5E7EB")),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#EEEEEE")),
        ("ALIGN", (3, 0), (4, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph('<font color="#555555">Total Outstanding</font>', muted))
    story.append(Paragraph(f"<b>₦{_money(total_outstanding)}</b>", ParagraphStyle(
        "total", parent=normal, fontName="Helvetica-Bold", fontSize=12, leading=14
    )))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "For clarification, contact Billing/Accounts Department. This document was generated from EDH HMS.",
        ParagraphStyle("footer", parent=muted, fontSize=8.5, leading=11),
    ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf
