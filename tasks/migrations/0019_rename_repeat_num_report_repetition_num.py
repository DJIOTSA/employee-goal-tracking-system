# Generated by Django 4.1.13 on 2024-02-20 06:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0018_report_repeat_option"),
    ]

    operations = [
        migrations.RenameField(
            model_name="report",
            old_name="repeat_num",
            new_name="repetition_num",
        ),
    ]
