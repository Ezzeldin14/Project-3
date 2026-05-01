from django.urls import path

from .views import ProcessImageView, SaveToHistoryView, DebugPingView

app_name = "ai_processing"

urlpatterns = [
    path("process/", ProcessImageView.as_view(), name="process_image"),
    path("save/", SaveToHistoryView.as_view(), name="save_to_history"),
    # path("ping/", DebugPingView.as_view(), name="debug_ping"),
]
