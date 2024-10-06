from django.contrib import admin
from .models import Recipe, Ingredient, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1  # Number of extra forms to display
    autocomplete_fields = ["ingredient"]


class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        RecipeIngredientInline,  # Use the new inline based on the intermediary model
    ]
    list_display = ("title", "author", "created_on", "updated_on")
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ["name"]  # Enables search functionality for autocomplete_fields


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
