from django.urls import path
from . import views

app_name = "pharmacy"

urlpatterns = [
    path("queue/", views.pharmacy_queue, name="queue"),
    path("add/<int:visit_id>/", views.add_prescription, name="add_prescription"),
    path("dispense/<int:item_id>/", views.mark_dispensed, name="mark_dispensed"),
]
