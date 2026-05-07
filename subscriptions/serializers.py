from rest_framework import serializers

from .models import Subscription, UsageRecord


class SubscriptionSerializer(serializers.ModelSerializer):
    """Read-only view of the user's subscription + quota info."""

    remaining_uses = serializers.SerializerMethodField()
    usage_in_cycle = serializers.SerializerMethodField()
    next_renewal = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'plan',
            'remaining_uses',
            'usage_in_cycle',
            'next_renewal',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_remaining_uses(self, obj: Subscription) -> int:
        return obj.get_remaining_uses()

    def get_usage_in_cycle(self, obj: Subscription) -> int:
        return obj.get_usage_in_current_cycle()

    def get_next_renewal(self, obj: Subscription):
        renewal = obj.get_next_renewal()
        if renewal:
            return renewal.isoformat()
        return None


class UsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageRecord
        fields = ('feature', 'used_at')
        read_only_fields = fields
