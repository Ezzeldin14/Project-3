from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_history', '0005_alter_user_history_feature_used'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user_history',
            name='feature_used',
            field=models.CharField(
                blank=True,
                choices=[
                    ('SUPER_RESOLUTION', 'Super Resolution'),
                    ('COLORIZATION', 'Colorization'),
                    ('DE_BLUR', 'Deblur'),
                    ('BILATERAL_FILTER', 'Bilateral Filter'),
                    ('GAUSSIAN_FILTER', 'Gaussian Filter'),
                    ('GUIDED_FILTER', 'Guided Filter'),
                    ('MEDIAN_FILTER', 'Median Filter'),
                ],
                max_length=50,
                null=True,
            ),
        ),
    ]
