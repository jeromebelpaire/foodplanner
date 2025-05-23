# Generated by Django 4.2.20 on 2025-04-18 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Ingredient",
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
                ("name", models.CharField(max_length=100, unique=True)),
                ("unit", models.CharField(max_length=50)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
    ]
