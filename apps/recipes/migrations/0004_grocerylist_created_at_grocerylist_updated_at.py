# Generated by Django 4.1.4 on 2023-06-18 13:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0003_grocerylist"),
    ]

    operations = [
        migrations.AddField(
            model_name="grocerylist",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="grocerylist",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
