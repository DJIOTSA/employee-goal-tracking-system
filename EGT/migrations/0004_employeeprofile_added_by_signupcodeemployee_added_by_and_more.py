# Generated by Django 4.1.13 on 2024-02-06 06:14

import EGT.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("EGT", "0003_administratorprofile_completion_bonus"),
    ]

    operations = [
        migrations.AddField(
            model_name="employeeprofile",
            name="added_by",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="signupcodeemployee",
            name="added_by",
            field=EGT.models.LowerCaseEmailField(
                max_length=254, null=True, verbose_name="added by: email address"
            ),
        ),
        migrations.AlterField(
            model_name="signupcodeemployee",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="new_employee",
                to=settings.AUTH_USER_MODEL,
                to_field="email",
            ),
        ),
    ]
