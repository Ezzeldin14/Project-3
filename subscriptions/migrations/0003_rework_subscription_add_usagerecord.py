# Generated manually — reworks Subscription model and adds UsageRecord

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
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
