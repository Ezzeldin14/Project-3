from django.urls import path

from .views import ProcessImageView

app_name = "ai_processing"

urlpatterns = [
    path("process/", ProcessImageView.as_view(), name="process_image"),
]
