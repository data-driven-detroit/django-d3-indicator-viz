# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_d3_indicator_viz', '0007_add_stacked_column_and_filter_option_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicatordatavisual',
            name='data_visual_type',
            field=models.TextField(
                blank=True,
                choices=[
                    ('ban', 'Ban'),
                    ('column', 'Column'),
                    ('donut', 'Donut'),
                    ('min_med_max', 'Min Med Max'),
                    ('line', 'Line'),
                    ('multiline', 'Multiline'),
                    ('stacked_column', 'Stacked Column'),
                    ('grouped_column', 'Grouped Column'),
                    ('quartile_line', 'Quartile Line'),
                ],
                null=True,
            ),
        ),
    ]
