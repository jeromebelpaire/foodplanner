from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .forms import RecipeForm
from .models import Ingredient, Recipe, GroceryList


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
            recipes = form.cleaned_data["recipes"]
            guests = request.POST.getlist("guests")
            ingredient_list = []
            for index, recipe in enumerate(recipes):
                ingredients = Ingredient.objects.filter(recipe=recipe)
                for ingredient in ingredients:
                    quantity = ingredient.quantity * int(guests[index])
                    ingredient_list.append({"name": ingredient.name, "quantity": quantity})
            return JsonResponse(ingredient_list, safe=False)

    form = RecipeForm()
    return render(request, "recipes/recipe_sum.html", {"form": form})


@login_required
@csrf_exempt
def save_grocery_list(request):
    if request.method == "POST":
        data = request.POST

        for recipe_id, guests in zip(data.getlist("recipes"), data.getlist("guests")):
            recipe = Recipe.objects.get(pk=recipe_id)
            GroceryList.objects.create(user=request.user, recipe=recipe, guests=guests)

        return JsonResponse({"success": True})


@login_required
def get_grocery_list(request):
    grocery_lists = GroceryList.objects.filter(user=request.user)
    ingredients = {}

    # Iterate over all grocery lists
    for grocery_list in grocery_lists:
        for ingredient in grocery_list.recipe.ingredients.all():
            quantity = ingredient.quantity * grocery_list.guests
            if ingredient.name in ingredients:
                ingredients[ingredient.name] += quantity
            else:
                ingredients[ingredient.name] = quantity

    return JsonResponse(ingredients)
