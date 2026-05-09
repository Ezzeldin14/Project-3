"""Replace Stripe fields with Paymob order ID on Subscription model."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_rework_subscription_add_usagerecord'),
    ]

    operations = [
        # Remove old Stripe fields
        migrations.RemoveField(
            model_name='subscription',
            name='stripe_customer_id',
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='stripe_subscription_id',
        ),
        # Add Paymob order ID
        migrations.AddField(
            model_name='subscription',
            name='paymob_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
