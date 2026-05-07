from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription
from .serializers import SubscriptionSerializer, UsageRecordSerializer


class SubscriptionStatusView(APIView):
    """
    GET /api/subscriptions/status/

    Returns the authenticated user's current plan, remaining AI-feature
    uses, and when the quota next renews.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription, _ = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'FREE'},
        )
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UsageHistoryView(APIView):
    """
    GET /api/subscriptions/usage/

    Returns the user's recent AI-feature usage records (last 20).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = request.user.usage_records.all()[:20]
        serializer = UsageRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
