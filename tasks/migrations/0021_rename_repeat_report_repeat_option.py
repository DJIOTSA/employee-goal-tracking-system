# Generated by Django 4.1.13 on 2024-02-20 13:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0020_rename_repeat_option_report_repeat"),
    ]

    operations = [
        migrations.RenameField(
            model_name="report",
            old_name="repeat",
            new_name="repeat_option",
        ),
    ]
