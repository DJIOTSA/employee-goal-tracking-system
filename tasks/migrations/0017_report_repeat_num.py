# Generated by Django 4.1.13 on 2024-02-19 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0016_activities_repetition_num_goal_repetition_num"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="repeat_num",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
