from django.urls import path

from .views import UserHistoryDetailView, UserHistoryListView

app_name = "user_history"

urlpatterns = [
    path("", UserHistoryListView.as_view(), name="history_list"),
    path("<int:pk>/", UserHistoryDetailView.as_view(), name="history_detail"),
]
