from django.urls import path
from . import views

app_name = "lab"

urlpatterns = [
    path("queue/", views.lab_queue, name="queue"),
    path("add/<int:visit_id>/", views.add_lab_request, name="add_lab_request"),
    path("result/<int:lab_request_id>/", views.upload_result, name="upload_result"),
]
