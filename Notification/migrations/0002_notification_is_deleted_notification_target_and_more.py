# Generated by Django 4.1.13 on 2024-02-19 23:49

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Notification", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="is_deleted",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="notification",
            name="target",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name="notification",
            name="recipient",
        ),
        migrations.AddField(
            model_name="notification",
            name="recipient",
            field=models.ManyToManyField(
                help_text="Those users concern with the notification",
                related_name="recipient_set",
                related_query_name="recipient",
                to=settings.AUTH_USER_MODEL,
                verbose_name="users",
            ),
        ),
    ]
