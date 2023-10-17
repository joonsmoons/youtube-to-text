# Generated by Django 4.2.6 on 2023-10-15 09:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Language",
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
                    "name",
                    models.CharField(
                        choices=[("English", "English"), ("Korean", "한국어")],
                        default="English",
                        max_length=20,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InputData",
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
                ("youtube_url", models.URLField()),
                ("start_time", models.CharField(max_length=10)),
                ("end_time", models.CharField(max_length=10)),
                (
                    "language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="generator.language",
                    ),
                ),
            ],
        ),
    ]
