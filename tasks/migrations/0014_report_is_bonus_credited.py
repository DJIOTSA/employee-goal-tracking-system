# Generated by Django 4.1.13 on 2024-02-12 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0013_rename_status_report_report_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="is_bonus_credited",
            field=models.BooleanField(default=False),
        ),
    ]
