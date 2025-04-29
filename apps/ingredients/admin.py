# apps/ingredients/admin.py
from django.contrib import admin
from .models import Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "fdc_id")
    search_fields = ("name",)
