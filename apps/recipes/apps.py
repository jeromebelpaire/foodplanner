from django.apps import AppConfig


class RecipesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.recipes"  # The new Python path to the app
    label = "recipes"  # The original app label (IMPORTANT!)
