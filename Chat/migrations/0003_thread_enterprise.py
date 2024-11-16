# Generated by Django 4.1.13 on 2024-02-29 09:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("EGT", "0006_alter_myuser_cv"),
        ("Chat", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="thread",
            name="enterprise",
            field=models.OneToOneField(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="EGT.enterprise",
            ),
            preserve_default=False,
        ),
    ]
