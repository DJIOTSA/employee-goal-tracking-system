# Generated by Django 4.1.13 on 2024-02-10 10:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tasks", "0011_alter_activities_status_alter_goal_status_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="activities",
            name="is_sold",
        ),
        migrations.RemoveField(
            model_name="goal",
            name="is_sold",
        ),
        migrations.AlterField(
            model_name="activities",
            name="employee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="worker",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="activities",
            name="is_done",
            field=models.IntegerField(
                blank=True, choices=[(0, "SUBMIT"), (1, "COMPLETED")], null=True
            ),
        ),
        migrations.AlterField(
            model_name="activities",
            name="status",
            field=models.IntegerField(
                blank=True,
                choices=[(0, "REJECTED"), (1, "ACCEPTED"), (2, "PENDING"), (3, "PAID")],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="goal",
            name="is_done",
            field=models.IntegerField(
                blank=True, choices=[(0, "SUBMIT"), (1, "COMPLETED")], null=True
            ),
        ),
        migrations.AlterField(
            model_name="goal",
            name="status",
            field=models.IntegerField(
                blank=True,
                choices=[(0, "REJECTED"), (1, "ACCEPTED"), (2, "PENDING"), (3, "PAID")],
                null=True,
            ),
        ),
    ]
