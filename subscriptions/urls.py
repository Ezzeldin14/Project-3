from django.urls import path

from .views import SubscriptionStatusView, UsageHistoryView

app_name = "subscriptions"

urlpatterns = [
    path("status/", SubscriptionStatusView.as_view(), name="subscription_status"),
    path("usage/", UsageHistoryView.as_view(), name="usage_history"),
]
