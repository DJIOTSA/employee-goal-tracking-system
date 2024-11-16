# Generated by Django 4.1.13 on 2024-02-07 09:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("EGT", "0005_alter_signupcodeemployee_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Activities",
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
                ("title", models.CharField(default="some text", max_length=200)),
                ("description", models.TextField(max_length=10000, null=True)),
                (
                    "starting_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("ending_date", models.DateTimeField(blank=True)),
                (
                    "attached_file",
                    models.FileField(
                        blank=True, null=True, upload_to="activities/files"
                    ),
                ),
                (
                    "attached_file1",
                    models.FileField(
                        blank=True, null=True, upload_to="activities/files"
                    ),
                ),
                (
                    "attached_file2",
                    models.FileField(
                        blank=True, null=True, upload_to="activities/files"
                    ),
                ),
                (
                    "bonus",
                    models.DecimalField(decimal_places=3, default=0, max_digits=10),
                ),
                (
                    "date_of_registration",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("is_done", models.BooleanField(default=False)),
                (
                    "repeat",
                    models.IntegerField(
                        choices=[
                            (0, "No"),
                            (1, "Daily"),
                            (2, "Weekly"),
                            (3, "Monthly"),
                        ],
                        default=0,
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "REJECTED"),
                            (1, "CREDITED"),
                            (2, "PENDING"),
                            (3, "PAID"),
                            (4, "DEACTIVATED"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="worker",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "employees",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Enterprise employee's in charge of the the activity. Those users will get activity assertion permissions",
                        related_name="employees_set",
                        related_query_name="employees",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="employees_in_charge",
                    ),
                ),
            ],
            options={
                "db_table": "Activities",
            },
        ),
        migrations.CreateModel(
            name="Goal",
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
                ("title", models.CharField(default="some text", max_length=200)),
                (
                    "description",
                    models.TextField(default="some text", max_length=10000),
                ),
                (
                    "attached_file",
                    models.FileField(blank=True, null=True, upload_to="goals/files"),
                ),
                (
                    "attached_file1",
                    models.FileField(blank=True, null=True, upload_to="goals/files"),
                ),
                (
                    "attached_file2",
                    models.FileField(blank=True, null=True, upload_to="goals/files"),
                ),
                (
                    "starting_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("ending_date", models.DateTimeField(blank=True)),
                (
                    "bonus",
                    models.DecimalField(
                        decimal_places=3, default=0.0, max_digits=10, null=True
                    ),
                ),
                (
                    "date_of_registration",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "important",
                    models.IntegerField(
                        choices=[
                            (1, "NORMAL"),
                            (2, "IMPORTANT"),
                            (3, "VERY_IMPORTANT"),
                        ],
                        default=1,
                    ),
                ),
                ("is_done", models.BooleanField(default=False)),
                (
                    "repeat",
                    models.IntegerField(
                        choices=[
                            (0, "No"),
                            (1, "Daily"),
                            (2, "Weekly"),
                            (3, "Monthly"),
                        ],
                        default=0,
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "REJECTED"),
                            (1, "CREDITED"),
                            (2, "PENDING"),
                            (3, "PAID"),
                            (4, "DEACTIVATED"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="creator",
                        to=settings.AUTH_USER_MODEL,
                        to_field="email",
                    ),
                ),
                (
                    "enterprise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="EGT.enterprise",
                        to_field="name",
                    ),
                ),
                (
                    "goal_manager",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="manager",
                        to=settings.AUTH_USER_MODEL,
                        to_field="email",
                    ),
                ),
                (
                    "users_in_charge",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Enterprise user's in charge of the the goal. Those users will get goal assertion permissions",
                        related_name="users_in_charge_set",
                        related_query_name="users_in_charge",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="users_in_charge",
                    ),
                ),
            ],
            options={
                "db_table": "Goals",
            },
        ),
        migrations.CreateModel(
            name="Report",
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
                    "report",
                    models.FileField(blank=True, null=True, upload_to="reports/files"),
                ),
                ("date_of_submission", models.DateTimeField(auto_now_add=True)),
                (
                    "option",
                    models.CharField(
                        choices=[("G", "GOAL"), ("A", "ACTIVITY")], max_length=1
                    ),
                ),
                (
                    "rate",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (0, "Null"),
                            (100, "Acceptable"),
                            (200, "Good"),
                            (300, "Very Good"),
                            (400, "Excellent"),
                            (500, "Perfect"),
                        ],
                        null=True,
                    ),
                ),
                ("submit_late", models.BooleanField(blank=True, null=True)),
                ("comment", models.TextField(blank=True, max_length=2000, null=True)),
                (
                    "activity",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tasks.activities",
                    ),
                ),
                (
                    "goal",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tasks.goal",
                    ),
                ),
                (
                    "rated_by",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluator",
                        to=settings.AUTH_USER_MODEL,
                        to_field="email",
                    ),
                ),
                (
                    "submit_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        to_field="email",
                    ),
                ),
            ],
            options={
                "db_table": "Reports",
            },
        ),
        migrations.AddField(
            model_name="activities",
            name="goal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="tasks.goal"
            ),
        ),
    ]
