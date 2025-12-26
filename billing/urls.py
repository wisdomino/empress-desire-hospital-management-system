from django.urls import path
from . import views
from . import dashboard_views
from . import claims_views
from . import pdf_views
from . import hmo_aging_views
from . import hmo_actions_views
from . import followup_views

app_name = "billing"

urlpatterns = [
    # Dashboard
    path("dashboard/", dashboard_views.revenue_dashboard, name="dashboard"),

    # Invoices
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:invoice_id>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<int:invoice_id>/pay/", views.add_payment, name="add_payment"),
    path("invoices/<int:invoice_id>/pdf/", pdf_views.invoice_pdf, name="invoice_pdf"),
    path(
        "invoices/<int:invoice_id>/receipt/<int:payment_id>/pdf/",
        pdf_views.receipt_pdf,
        name="receipt_pdf",
    ),

    # Claims
    path("claims/", claims_views.claim_batch_list, name="claim_batch_list"),
    path("claims/new/", claims_views.claim_batch_create, name="claim_batch_create"),
    path("claims/<int:batch_id>/", claims_views.claim_batch_detail, name="claim_batch_detail"),
    path("claims/<int:batch_id>/add/", claims_views.claim_batch_add_invoices, name="claim_batch_add_invoices"),
    path("claims/<int:batch_id>/export/", claims_views.claim_batch_export_csv, name="claim_batch_export_csv"),
    path("claims/<int:batch_id>/submit/", claims_views.claim_batch_submit, name="claim_batch_submit"),
    path("claims/<int:batch_id>/paid/", claims_views.claim_batch_mark_paid, name="claim_batch_mark_paid"),
    path("claims/<int:batch_id>/cover/pdf/", pdf_views.claim_cover_pdf, name="claim_cover_pdf"),

    # HMO Aging & Actions
    path("hmo-aging/", hmo_aging_views.hmo_aging_dashboard, name="hmo_aging"),
    path("hmo-aging/dispute/<int:invoice_id>/", hmo_actions_views.mark_invoice_disputed, name="mark_invoice_disputed"),
    path(
        "hmo-aging/dispute/<int:invoice_id>/clear/",
        hmo_actions_views.clear_invoice_dispute,
        name="clear_invoice_dispute",
    ),
    path("claims/item/<int:item_id>/dispute/", hmo_actions_views.flag_claim_item_disputed, name="flag_claim_item_disputed"),
    path("hmo-aging/reminded/", hmo_actions_views.mark_hmo_reminded, name="mark_hmo_reminded"),

    # HMO PDFs
    path("hmo/reminder/<str:hmo_name>/pdf/", pdf_views.hmo_reminder_letter_pdf, name="hmo_reminder_pdf"),
    path("hmo/disputes/<str:hmo_name>/pdf/", pdf_views.hmo_dispute_sheet_pdf, name="hmo_disputes_pdf"),

    # ✅ Follow-ups 
    path("followups/", followup_views.followups_list, name="followups_list"),
]
