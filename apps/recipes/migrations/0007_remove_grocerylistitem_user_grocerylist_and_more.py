# Generated by Django 4.1.4 on 2023-06-18 20:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("recipes", "0006_rename_grocery_list_to_grocery_list_item"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="grocerylistitem",
            name="user",
        ),
        migrations.CreateModel(
            name="GroceryList",
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
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="grocerylistitem",
            name="grocery_list",
            field=models.ForeignKey(
                default=999,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="recipes.grocerylist",
            ),
            preserve_default=False,
        ),
    ]
