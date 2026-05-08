from django.contrib import admin
from django.utils.html import format_html
from .models import User, EmailVerificationOTP, PasswordResetOTP
from subscriptions.models import Subscription


admin.site.site_header = "PixRevive Admin Portal"
admin.site.site_title = "My Project PixRevive Admin Portal"
admin.site.index_title = "Welcome to PixRevive Admin Portal"


class SubscriptionInline(admin.StackedInline):
    """Show the subscription plan inline on the User detail page."""
    model = Subscription
    extra = 0
    max_num = 1
    can_delete = False
    fields = ('plan',)
    verbose_name = 'Subscription Plan'
    verbose_name_plural = 'Subscription Plan'


@admin.action(description="⬆️ Upgrade selected users to PRO")
def upgrade_users_to_pro(modeladmin, request, queryset):
    count = 0
    for user in queryset:
        sub, _ = Subscription.objects.get_or_create(
            user=user, defaults={'plan': 'FREE'}
        )
        if sub.plan != 'PRO':
            sub.plan = 'PRO'
            sub.save()
            count += 1
    modeladmin.message_user(request, f"✅ {count} user(s) upgraded to PRO.")


@admin.action(description="⬇️ Downgrade selected users to FREE")
def downgrade_users_to_free(modeladmin, request, queryset):
    count = 0
    for user in queryset:
        sub, _ = Subscription.objects.get_or_create(
            user=user, defaults={'plan': 'FREE'}
        )
        if sub.plan != 'FREE':
            sub.plan = 'FREE'
            sub.save()
            count += 1
    modeladmin.message_user(request, f"✅ {count} user(s) downgraded to FREE.")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'get_plan',
        'is_verified',
    )
    list_filter = ('is_verified',)
    search_fields = ('email', 'username')
    inlines = [SubscriptionInline]
    actions = [upgrade_users_to_pro, downgrade_users_to_free]

    def get_plan(self, obj):
        try:
            sub = Subscription.objects.filter(user=obj).first()
            plan = sub.plan if sub else 'FREE'
        except Exception:
            plan = 'FREE'

        if plan == 'PRO':
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:3px 10px;'
                'border-radius:12px;font-weight:bold;font-size:11px;">PRO</span>'
            )
        return format_html(
            '<span style="background:#6b7280;color:#fff;padding:3px 10px;'
            'border-radius:12px;font-weight:bold;font-size:11px;">FREE</span>'
        )
    get_plan.short_description = 'Plan'


admin.site.register(EmailVerificationOTP)
admin.site.register(PasswordResetOTP)