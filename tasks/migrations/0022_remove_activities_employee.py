# Generated by Django 4.1.13 on 2024-02-21 12:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0021_rename_repeat_report_repeat_option"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="activities",
            name="employee",
        ),
    ]
