"""
Auto-create a FREE subscription for every new user.
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_free_subscription(sender, instance, created, **kwargs):
    if created:
        from .models import Subscription
        Subscription.objects.get_or_create(
            user=instance,
            defaults={'plan': 'FREE'},
        )
