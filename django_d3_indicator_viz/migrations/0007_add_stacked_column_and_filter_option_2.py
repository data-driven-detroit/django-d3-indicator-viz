# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_d3_indicator_viz', '0006_alter_indicatordatavisual_data_visual_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicatorvalue',
            name='filter_option_2',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='indicator_values_secondary',
                to='django_d3_indicator_viz.indicatorfilteroption',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='indicatorvalue',
            unique_together={
                ('source', 'start_date', 'end_date', 'indicator', 'filter_option', 'filter_option_2', 'location'),
            },
        ),
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
                    ('quartile_line', 'Quartile Line'),
                ],
                null=True,
            ),
        ),
    ]
