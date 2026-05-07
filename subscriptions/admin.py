from django.contrib import admin

from .models import Subscription, UsageRecord


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'created_at', 'updated_at')
    list_filter = ('plan',)
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'feature', 'used_at')
    list_filter = ('feature',)
    search_fields = ('user__email',)
    readonly_fields = ('used_at',)