# Generated manually — reworks Subscription model and adds UsageRecord

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def remove_duplicate_subscriptions(apps, schema_editor):
    """
    Before converting ForeignKey → OneToOneField, remove duplicate
    subscriptions so each user has at most one row.
    Keeps the most recent subscription per user.
    """
    Subscription = apps.get_model('subscriptions', 'Subscription')
    from django.db.models import Max

    # Find users with more than one subscription
    dupes = (
        Subscription.objects.values('user_id')
        .annotate(max_id=Max('id'), cnt=models.Count('id'))
        .filter(cnt__gt=1)
    )
    for entry in dupes:
        # Keep the row with the highest id, delete the rest
        Subscription.objects.filter(
            user_id=entry['user_id']
        ).exclude(id=entry['max_id']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 0. Remove duplicate subscriptions before OneToOne conversion ──
        migrations.RunPython(
            remove_duplicate_subscriptions,
            migrations.RunPython.noop,
        ),

        # ── 1. Drop old columns that no longer exist ──
        migrations.RemoveField(
            model_name='subscription',
            name='start_date',
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='active',
        ),

        # ── 2. Alter plan choices (FREE/PRO instead of FREE/PREMIUM) ──
        migrations.AlterField(
            model_name='subscription',
            name='plan',
            field=models.CharField(
                choices=[('FREE', 'Free'), ('PRO', 'Pro')],
                default='FREE',
                max_length=10,
            ),
        ),

        # ── 3. Add new timestamp fields ──
        migrations.AddField(
            model_name='subscription',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default='2025-01-01T00:00:00Z'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscription',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # ── 4. Add stripe_customer_id ──
        migrations.AddField(
            model_name='subscription',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),

        # ── 5. Change user FK → OneToOneField ──
        migrations.AlterField(
            model_name='subscription',
            name='user',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='subscription',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # ── 6. Set table name ──
        migrations.AlterModelTable(
            name='subscription',
            table='subscriptions',
        ),

        # ── 7. Create UsageRecord ──
        migrations.CreateModel(
            name='UsageRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature', models.CharField(max_length=50)),
                ('used_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='usage_records',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'usage_records',
                'ordering': ['-used_at'],
            },
        ),
    ]
