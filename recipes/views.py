from django.shortcuts import get_object_or_404, render

from .forms import RecipeForm
from .models import Ingredient, Recipe


def home_view(request):
    recipes = Recipe.objects.order_by("-created_on")[:9]
    context = {"recipes": recipes}
    return render(request, "recipes/home.html", context)


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


def recipe_sum_view(request):
    if request.method == "POST":
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.cleaned_data["recipe"]
            guests = form.cleaned_data["guests"]
            ingredients = Ingredient.objects.filter(recipe=recipe)
            scaled_ingredients = []
            for ingredient in ingredients:
                scaled_ingredients.append(
                    {"name": ingredient.name, "quantity": ingredient.quantity * guests}
                )
            return render(
                request,
                "recipes/recipe_sum.html",
                {"form": form, "ingredients": scaled_ingredients},
            )

    form = RecipeForm()
    return render(request, "recipes/recipe_sum.html", {"form": form})
