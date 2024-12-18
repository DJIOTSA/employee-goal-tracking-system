# Generated by Django 4.1.13 on 2024-02-21 06:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Notification", "0004_notification_user"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="recipient",
        ),
        migrations.AlterField(
            model_name="notification",
            name="user",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]
