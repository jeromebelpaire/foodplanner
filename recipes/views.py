from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse, get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from .forms import GroceryListForm, RecipeForm
from .models import GroceryList, PlannedRecipe, Ingredient, Recipe


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


def ajax_test(request):
    if is_ajax(request=request):
        message = "This is ajax"
    else:
        message = "Not ajax"
    return HttpResponse(message)


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
    if is_ajax(request):
        if "grocery_list" in request.POST:
            grocery_list_id = request.POST.get("grocery_list")
            grocery_list = GroceryList.objects.get(id=grocery_list_id)
            # Create a new RecipeForm populated with the recipes from the selected grocery list
            recipe_form = RecipeForm(initial={"recipes": Recipe.objects.all()})
            recipe_form_html = render_to_string(
                "recipes/recipe_form.html", {"form": recipe_form}, request=request
            )
            return JsonResponse({"recipe_form_html": recipe_form_html})

    # First, initialize both forms
    grocery_list_form = GroceryListForm(user=request.user)
    recipe_form = RecipeForm()

    # If this is a POST request, validate and process the forms
    if request.method == "POST":
        grocery_list_form = GroceryListForm(request.POST, user=request.user)
        recipe_form = RecipeForm(request.POST)

        if grocery_list_form.is_valid() and recipe_form.is_valid():
            selected_grocery_list = grocery_list_form.cleaned_data["grocery_list"]
            selected_recipes = recipe_form.cleaned_data["recipes"]

            # Assuming 'guests' is an input field from the RecipeForm
            guests = request.POST.getlist("guests")

            # Add the selected recipes to the grocery list
            for index, recipe in enumerate(selected_recipes):
                ingredients = Ingredient.objects.filter(recipe=recipe)
                for ingredient in ingredients:
                    quantity = ingredient.quantity * int(guests[index])
                    PlannedRecipe.objects.create(
                        grocery_list=selected_grocery_list, recipe=recipe, guests=int(guests[index])
                    )

            # Now retrieve all ingredients from the selected grocery list
            planned_recipes = PlannedRecipe.objects.filter(grocery_list=selected_grocery_list)
            ingredients = {}
            for planned_recipe in planned_recipes:
                for ingredient in planned_recipe.recipe.ingredients.all():
                    quantity = ingredient.quantity * planned_recipe.guests
                    if ingredient.name in ingredients:
                        ingredients[ingredient.name] += quantity
                    else:
                        ingredients[ingredient.name] = quantity

            return JsonResponse(ingredients, safe=False)

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
    if grocery_list_id:
        grocery_list = GroceryList.objects.get(id=grocery_list_id)
    else:
        grocery_list, created = GroceryList.objects.get_or_create(user=request.user)

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
