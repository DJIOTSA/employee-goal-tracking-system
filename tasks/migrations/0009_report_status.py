# Generated by Django 4.1.13 on 2024-02-09 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0008_activities_sold_to"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "REJECTED"),
                    (1, "CREDITED"),
                    (2, "PENDING"),
                    (3, "PAID"),
                    (4, "DEACTIVATED"),
                ],
                null=True,
            ),
        ),
    ]