from django.contrib import admin
from .models import User, EmailVerificationOTP, PasswordResetOTP
from subscriptions.models import Subscription


admin.site.site_header = "PixRevive Admin Portal"
admin.site.site_title = "My Project PixRevive Admin Portal"
admin.site.index_title = "Welcome to PixRevive Admin Portal"


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    max_num = 1
    can_delete = False
    fields = ('plan',)


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
    modeladmin.message_user(request, f"{count} user(s) upgraded to PRO.")

upgrade_users_to_pro.short_description = "Upgrade selected users to PRO"


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
    modeladmin.message_user(request, f"{count} user(s) downgraded to FREE.")

downgrade_users_to_free.short_description = "Downgrade selected users to FREE"


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('email', 'username')
    inlines = [SubscriptionInline]
    actions = [upgrade_users_to_pro, downgrade_users_to_free]


admin.site.register(User, UserAdmin)
admin.site.register(EmailVerificationOTP)
admin.site.register(PasswordResetOTP)