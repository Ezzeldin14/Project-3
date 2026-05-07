from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    """
    Tracks a user's subscription plan and enforces usage quotas.

    FREE plan:  2 AI-feature uses per 2-day rolling window.
    PRO  plan:  unlimited.
    """

    PLAN_CHOICES = [
        ('FREE', 'Free'),
        ('PRO', 'Pro'),
    ]

    # Free-plan quota constants
    FREE_PLAN_LIMIT = 2          # max uses per cycle
    FREE_PLAN_CYCLE_DAYS = 2     # rolling window in days

    # AI features that consume quota on the free plan
    RATE_LIMITED_FEATURES = frozenset({
        'COLORIZATION', 'DE_NOISE', 'DE_BLUR', 'SUPER_RESOLUTION',
    })

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='FREE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stripe identifiers (populated when user upgrades to PRO)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.user.email} — {self.plan}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def is_pro(self) -> bool:
        return self.plan == 'PRO'

    def _cycle_start(self):
        return timezone.now() - timedelta(days=self.FREE_PLAN_CYCLE_DAYS)

    def get_usage_in_current_cycle(self) -> int:
        """Count rate-limited feature uses in the current 2-day window."""
        return UsageRecord.objects.filter(
            user=self.user,
            feature__in=self.RATE_LIMITED_FEATURES,
            used_at__gte=self._cycle_start(),
        ).count()

    def get_remaining_uses(self) -> int:
        """Remaining AI-feature uses in this cycle (∞ for PRO)."""
        if self.is_pro:
            return 999_999  # effectively unlimited
        return max(0, self.FREE_PLAN_LIMIT - self.get_usage_in_current_cycle())

    def can_use_feature(self, feature: str) -> bool:
        """Return True if the user is allowed to use *feature* right now."""
        if self.is_pro:
            return True
        if feature not in self.RATE_LIMITED_FEATURES:
            return True  # basic filters are always free
        return self.get_remaining_uses() > 0

    def get_next_renewal(self):
        """
        Return the datetime when the oldest usage record in the current
        window expires (i.e. when one slot frees up).  Returns None if
        there is nothing to renew.
        """
        earliest = UsageRecord.objects.filter(
            user=self.user,
            feature__in=self.RATE_LIMITED_FEATURES,
            used_at__gte=self._cycle_start(),
        ).order_by('used_at').first()
        if earliest:
            return earliest.used_at + timedelta(days=self.FREE_PLAN_CYCLE_DAYS)
        return None

    def record_usage(self, feature: str) -> 'UsageRecord':
        """Create a UsageRecord for the given feature."""
        return UsageRecord.objects.create(user=self.user, feature=feature)


class UsageRecord(models.Model):
    """Logs every AI-feature invocation for quota enforcement."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_records',
    )
    feature = models.CharField(max_length=50)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usage_records'
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.user.email} — {self.feature} @ {self.used_at:%Y-%m-%d %H:%M}"
