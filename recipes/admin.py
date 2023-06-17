from django.contrib import admin
from .models import Recipe, Ingredient


class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1  # Number of extra blank lines to display


class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        IngredientInline,
    ]
    list_display = ("title", "author", "created_on", "updated_on")
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient)
