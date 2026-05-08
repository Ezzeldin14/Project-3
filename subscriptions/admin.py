from django.contrib import admin
from .models import Subscription, UsageRecord


def upgrade_to_pro(modeladmin, request, queryset):
    updated = queryset.update(plan='PRO')
    modeladmin.message_user(request, f"{updated} subscription(s) upgraded to PRO.")

upgrade_to_pro.short_description = "Upgrade selected to PRO"


def downgrade_to_free(modeladmin, request, queryset):
    updated = queryset.update(plan='FREE')
    modeladmin.message_user(request, f"{updated} subscription(s) downgraded to FREE.")

downgrade_to_free.short_description = "Downgrade selected to FREE"


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'created_at', 'updated_at')
    list_filter = ('plan',)
    search_fields = ('user__email', 'user__username')
    list_editable = ('plan',)
    actions = [upgrade_to_pro, downgrade_to_free]


class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'feature', 'used_at')
    list_filter = ('feature',)
    search_fields = ('user__email',)


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(UsageRecord, UsageRecordAdmin)