# Generated by Django 4.1.13 on 2024-02-11 19:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0012_remove_activities_is_sold_remove_goal_is_sold_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="report",
            old_name="status",
            new_name="report_status",
        ),
    ]
