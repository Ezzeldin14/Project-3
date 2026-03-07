from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import User_History
from .serializers import UserHistorySerializer


class UserHistoryListView(generics.ListAPIView):
    """
    GET /api/history/

    Returns the authenticated user's processing history, most recent first.
    """
    serializer_class = UserHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User_History.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class UserHistoryDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/history/<id>/    — view a single history entry
    DELETE /api/history/<id>/ — delete a history entry
    """
    serializer_class = UserHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User_History.objects.filter(user=self.request.user)
