# Generated by Django 4.1.13 on 2024-02-07 19:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="rated_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="evaluator",
                to=settings.AUTH_USER_MODEL,
                to_field="email",
            ),
        ),
    ]
