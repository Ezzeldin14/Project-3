from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'currency')
    search_fields = ('user__email', 'reference_id')
    readonly_fields = ('id', 'created_at', 'updated_at')