# Generated by Django 4.1.13 on 2024-02-21 14:04

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tasks", "0022_remove_activities_employee"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activities",
            name="employees",
            field=models.ManyToManyField(
                blank=True,
                help_text="Enterprise employee's in charge of the the activity. Those users will get activity assertion permissions",
                related_name="employees_set",
                related_query_name="employees",
                to=settings.AUTH_USER_MODEL,
                verbose_name="employees",
            ),
        ),
    ]
