# Generated by Django 4.1.13 on 2024-03-02 08:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Chat", "0006_alter_message_recipient"),
    ]

    operations = [
        migrations.CreateModel(
            name="Chat",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("is_group", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="ChatRoom",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "chat",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="Chat.chat"
                    ),
                ),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="Chat.message"
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="threadmessage",
            name="message",
        ),
        migrations.RemoveField(
            model_name="threadmessage",
            name="thread",
        ),
        migrations.DeleteModel(
            name="Thread",
        ),
        migrations.DeleteModel(
            name="ThreadMessage",
        ),
        migrations.AddField(
            model_name="chat",
            name="messages",
            field=models.ManyToManyField(through="Chat.ChatRoom", to="Chat.message"),
        ),
        migrations.AddField(
            model_name="chat",
            name="participants",
            field=models.ManyToManyField(
                related_name="chats", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
