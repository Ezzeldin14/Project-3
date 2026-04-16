from django.urls import path

from .views import ProcessImageView, DebugPingView

app_name = "ai_processing"

urlpatterns = [
    path("process/", ProcessImageView.as_view(), name="process_image"),
    path("ping/", DebugPingView.as_view(), name="debug_ping"),
]
