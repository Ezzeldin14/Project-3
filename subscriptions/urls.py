from django.urls import path

from .views import SubscriptionStatusView, UsageHistoryView, PaymobWebhookView, VerifyPaymentView

app_name = "subscriptions"

urlpatterns = [
    path("status/", SubscriptionStatusView.as_view(), name="subscription_status"),
    path("usage/", UsageHistoryView.as_view(), name="usage_history"),
    path("paymob-webhook/", PaymobWebhookView.as_view(), name="paymob_webhook"),
    path("verify-payment/", VerifyPaymentView.as_view(), name="verify_payment"),
]
