# Generated by Django 4.1.13 on 2024-02-01 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("EGT", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="enterprise",
            name="fund",
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=100),
        ),
    ]