from django.shortcuts import render, get_object_or_404
from .models import Recipe, Ingredient


def recipe_view(request, recipe_slug, guests=1):
    recipe = get_object_or_404(Recipe, slug=recipe_slug)
    ingredients = Ingredient.objects.filter(recipe=recipe)

    scaled_ingredients = []
    for ingredient in ingredients:
        scaled_ingredients.append(
            {"name": ingredient.name, "quantity": ingredient.quantity * guests}
        )

    context = {"recipe": recipe, "ingredients": scaled_ingredients}

    return render(request, "recipes/recipe.html", context)
