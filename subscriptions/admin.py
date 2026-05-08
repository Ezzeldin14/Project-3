from django.contrib import admin
from django.utils.html import format_html

from .models import Subscription, UsageRecord


@admin.action(description="⬆️ Upgrade selected to PRO")
def upgrade_to_pro(modeladmin, request, queryset):
    updated = queryset.exclude(plan='PRO').update(plan='PRO')
    modeladmin.message_user(request, f"✅ {updated} subscription(s) upgraded to PRO.")


@admin.action(description="⬇️ Downgrade selected to FREE")
def downgrade_to_free(modeladmin, request, queryset):
    updated = queryset.exclude(plan='FREE').update(plan='FREE')
    modeladmin.message_user(request, f"✅ {updated} subscription(s) downgraded to FREE.")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'username',
        'plan_badge',
        'remaining_uses_display',
        'created_at',
        'updated_at',
    )
    list_filter = ('plan',)
    list_editable = ('plan_badge',)  # removed — we use actions instead
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'remaining_uses_display')
    actions = [upgrade_to_pro, downgrade_to_free]

    # Make plan editable directly in the list view
    list_editable = []  # plan is shown via plan_badge (read-only display)

    # ---- custom columns ----
    @admin.display(description='Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Username', ordering='user__username')
    def username(self, obj):
        return obj.user.username

    @admin.display(description='Plan')
    def plan_badge(self, obj):
        if obj.plan == 'PRO':
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:3px 10px;'
                'border-radius:12px;font-weight:bold;font-size:11px;">PRO</span>'
            )
        return format_html(
            '<span style="background:#6b7280;color:#fff;padding:3px 10px;'
            'border-radius:12px;font-weight:bold;font-size:11px;">FREE</span>'
        )

    @admin.display(description='Remaining Uses')
    def remaining_uses_display(self, obj):
        remaining = obj.get_remaining_uses()
        if obj.is_pro:
            return format_html(
                '<span style="color:#10b981;font-weight:bold;">∞ Unlimited</span>'
            )
        color = '#ef4444' if remaining == 0 else '#f59e0b' if remaining == 1 else '#10b981'
        return format_html(
            '<span style="color:{};font-weight:bold;">{} / {}</span>',
            color, remaining, Subscription.FREE_PLAN_LIMIT,
        )

    # Allow changing plan from the detail (edit) page
    fields = ('user', 'plan', 'stripe_customer_id', 'stripe_subscription_id',
              'remaining_uses_display', 'created_at', 'updated_at')


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'feature', 'used_at')
    list_filter = ('feature',)
    search_fields = ('user__email',)
    readonly_fields = ('used_at',)