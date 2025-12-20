from django.urls import path
from . import views
from . import pdf_views

app_name = "visits"

urlpatterns = [
    path("queue/", views.queue, name="queue"),
    path("start/<int:patient_id>/", views.start_visit, name="start_visit"),
    path("<int:visit_id>/", views.visit_detail, name="visit_detail"),
    path("<int:visit_id>/vitals/", views.vitals_update, name="vitals_update"),
    path("<int:visit_id>/take/", views.doctor_take_case, name="doctor_take_case"),
    path("<int:visit_id>/consultation/", views.consultation, name="consultation"),
    path("<int:visit_id>/close/", views.close_visit, name="close_visit"),
    path("<int:visit_id>/emergency-pdf/", pdf_views.emergency_summary_pdf, name="emergency_pdf"),

]
