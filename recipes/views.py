from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from .forms import GroceryListForm, RecipeForm
from .models import GroceryList, PlannedRecipe, Ingredient, Recipe


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


@login_required
@csrf_exempt
def create_grocery_list(request):
    if request.method == "POST":
        name = request.POST.get("name")
        grocery_list = GroceryList(name=name, user=request.user)
        grocery_list.save()
        return JsonResponse({"message": "Grocery list created successfully!"}, status=201)
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)


def generate_recipe_select_form(request):
    if "grocery_list" in request.POST:
        grocery_list_id = request.POST.get("grocery_list")
        grocery_list = GroceryList.objects.get(id=grocery_list_id)
        # Create a new RecipeForm populated with the recipes from the selected grocery list
        recipe_form = RecipeForm(initial={"recipes": Recipe.objects.all()})
        recipe_form_html = render_to_string(
            "recipes/recipe_form.html", {"form": recipe_form}, request=request
        )
        return JsonResponse({"recipe_form_html": recipe_form_html})
    else:
        raise ValueError(f"Unkown grocery_list_id in: {request.POST}")


def recipe_sum_view(request):
    # First, initialize both forms
    grocery_list_form = GroceryListForm(user=request.user)
    recipe_form = RecipeForm()

    return render(
        request,
        "recipes/recipe_sum.html",
        {"grocery_list_form": grocery_list_form, "recipe_form": recipe_form},
    )


@login_required
@csrf_exempt
def save_planned_recipe(request):
    if request.method == "POST":
        data = request.POST

        for grocery_list_id, recipe_id, guests in zip(
            data.getlist("grocery_list"),
            data.getlist("recipes"),
            data.getlist("guests"),
        ):
            recipe = Recipe.objects.get(pk=recipe_id)
            PlannedRecipe.objects.create(
                grocery_list_id=grocery_list_id, recipe=recipe, guests=guests
            )

        return JsonResponse({"success": True})


@login_required
def get_planned_ingredients(request, grocery_list_id=None):
    grocery_list = GroceryList.objects.get(id=grocery_list_id)

    grocery_list_items = PlannedRecipe.objects.filter(grocery_list=grocery_list)
    ingredients = {}

    # Iterate over all grocery lists
    for grocery_list_item in grocery_list_items:
        for ingredient in grocery_list_item.recipe.ingredients.all():
            quantity = ingredient.quantity * grocery_list_item.guests
            if ingredient.name in ingredients:
                ingredients[ingredient.name] += quantity
            else:
                ingredients[ingredient.name] = quantity

    return JsonResponse(ingredients)
