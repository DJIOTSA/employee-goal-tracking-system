# Generated by Django 4.1.13 on 2024-02-17 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0014_report_is_bonus_credited"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="transaction_id",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
