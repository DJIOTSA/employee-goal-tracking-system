# Generated by Django 4.1.13 on 2024-02-17 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payroll", "0003_transaction_is_deleted_delete_payroll"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
    ]
