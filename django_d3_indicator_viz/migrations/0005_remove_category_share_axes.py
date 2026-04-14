from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "django_d3_indicator_viz",
            "0004_remove_indicatordatavisual_source_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="category",
            name="share_axes",
        ),
    ]
