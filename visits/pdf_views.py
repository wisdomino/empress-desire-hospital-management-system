from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Visit

def emergency_summary_pdf(request, visit_id):
    visit = Visit.objects.select_related("patient").get(id=visit_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=emergency_summary.pdf"

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 50, "EMERGENCY SUMMARY")

    p.setFont("Helvetica", 11)
    p.drawString(50, height - 90, f"Patient: {visit.patient}")
    p.drawString(50, height - 110, f"Visit ID: {visit.visit_number}")
    p.drawString(50, height - 130, f"Diagnosis: {visit.diagnosis_primary or 'N/A'}")

    p.drawString(50, height - 170, "Doctor Notes:")
    text = p.beginText(50, height - 190)
    for line in (visit.doctor_notes or "").splitlines():
        text.textLine(line)
    p.drawText(text)

    p.showPage()
    p.save()

    return response

