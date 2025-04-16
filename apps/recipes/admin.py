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

    def get_queryset(self, request):
        qs = super(RecipeAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["author"].initial = request.user
        if not request.user.is_superuser:
            form.base_fields["author"].disabled = True
        return form


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ["name"]  # Enables search functionality for autocomplete_fields


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
