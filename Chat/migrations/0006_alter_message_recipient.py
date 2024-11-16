# Generated by Django 4.1.13 on 2024-03-02 06:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Chat", "0005_alter_thread_enterprise_alter_threadmessage_message"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="recipient",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="received_messages",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]