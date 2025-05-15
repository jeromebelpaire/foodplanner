from django.contrib import admin
from .models import Recipe, RecipeIngredient, RecipeRating


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ["ingredient"]


class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        RecipeIngredientInline,
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


class RecipeRatingAdmin(admin.ModelAdmin):
    list_display = ("recipe", "author", "rating", "created_on", "updated_on")
    search_fields = ["recipe__title", "author__username"]
    list_filter = ["recipe", "author"]


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeRating, RecipeRatingAdmin)
