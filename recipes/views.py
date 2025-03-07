from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from .forms import GroceryListForm, RecipeForm, ExtrasForm
from .models import GroceryList, PlannedRecipe, Recipe, PlannedExtra, Ingredient


@login_required
def home_view(request):
    recipes = Recipe.objects.order_by("-created_on")[:9]
    context = {"recipes": recipes}
    return render(request, "recipes/home.html", context)


@login_required
def recipe_view(request, recipe_slug, guests=1):
    recipe = get_object_or_404(Recipe, slug=recipe_slug)
    recipe_ingredients = recipe.recipeingredient_set.all()

    scaled_ingredients = []
    for ri in recipe_ingredients:
        quantity = ri.quantity * guests
        scaled_ingredients.append(f"{ri.ingredient.name}: {quantity:.2f} {ri.ingredient.unit}")

    context = {"recipe": recipe, "ingredients": scaled_ingredients}

    return render(request, "recipes/recipe.html", context)


@login_required
def get_formatted_ingredients(request, recipe_slug, guests=1):
    recipe = get_object_or_404(Recipe, slug=recipe_slug)
    recipe_ingredients = recipe.recipeingredient_set.all()

    scaled_ingredients = []
    for ri in recipe_ingredients:
        quantity = ri.quantity * guests
        scaled_ingredients.append(f"{ri.ingredient.name}: {quantity:.2f} {ri.ingredient.unit}")

    ingredients = {"recipe": recipe.title, "ingredients": scaled_ingredients}

    return JsonResponse(ingredients)


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
    # TODO make DRY
    if "grocery_list" in request.POST:
        # Create a new RecipeForm populated with the recipes from the selected grocery list
        recipe_form = RecipeForm(initial={"recipes": Recipe.objects.all()})
        extras_form = ExtrasForm(initial={"ingredients": Ingredient.objects.all()})
        recipe_form_html = render_to_string("recipes/recipe_form.html", {"form": recipe_form}, request=request)
        extras_form_html = render_to_string("recipes/extras_form.html", {"form": extras_form}, request=request)
        return JsonResponse({"recipe_form_html": recipe_form_html, "extras_form_html": extras_form_html})
    else:
        raise ValueError(f"Unkown grocery_list_id in: {request.POST}")


@login_required
def delete_grocery_list(request):
    grocery_list_id = request.POST.get("grocery_list")  # Use POST instead of GET
    try:
        grocery_list = GroceryList.objects.get(id=grocery_list_id)
        grocery_list.delete()
        return JsonResponse({"success": True})
    except GroceryList.DoesNotExist:
        return JsonResponse({"error": "GroceryList not found"}, status=404)  # Send an error response


@login_required
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
def save_planned_recipe(request):
    if request.method == "POST":
        data = request.POST

        for grocery_list_id, recipe_id, guests in zip(
            data.getlist("grocery_list"),
            data.getlist("recipes"),
            data.getlist("guests"),
        ):
            recipe = Recipe.objects.get(pk=recipe_id)
            PlannedRecipe.objects.create(grocery_list_id=grocery_list_id, recipe=recipe, guests=guests)

        return JsonResponse({"success": True})


@login_required
def save_planned_extra(request):
    if request.method == "POST":
        data = request.POST

        for grocery_list_id, ingredient_id, quantity in zip(
            data.getlist("grocery_list"),
            data.getlist("extras"),
            data.getlist("quantity"),
        ):
            ingredient = Ingredient.objects.get(pk=ingredient_id)
            PlannedExtra.objects.create(grocery_list_id=grocery_list_id, ingredient=ingredient, quantity=quantity)

        return JsonResponse({"success": True})


@login_required
def get_planned_ingredients(request):
    grocery_list_id = request.GET.get("grocery_list")
    grocery_list = GroceryList.objects.get(id=grocery_list_id)

    planned_recipes = PlannedRecipe.objects.filter(grocery_list=grocery_list)
    planned_extras = PlannedExtra.objects.filter(grocery_list=grocery_list)
    ingredients = {}

    # Iterate over all planned recipes and planned extrats
    for planned_recipe in planned_recipes:
        from_recipes_text = f"{planned_recipe.guests}p {planned_recipe.recipe.title}"

        for ri in planned_recipe.recipe.recipeingredient_set.all():
            quantity = ri.quantity * planned_recipe.guests
            if ri.ingredient.name in ingredients:
                ingredients[ri.ingredient.name]["quantity"] += quantity
                ingredients[ri.ingredient.name]["from_recipe"] += f" & {from_recipes_text}"
            else:
                ingredients[ri.ingredient.name] = {}
                ingredients[ri.ingredient.name]["quantity"] = quantity
                ingredients[ri.ingredient.name]["unit"] = ri.ingredient.unit  # FIXME
                ingredients[ri.ingredient.name]["from_recipe"] = from_recipes_text

    from_recipes_text += " Extras:" if len(planned_extras) > 0 else ""

    for pe in planned_extras:
        quantity = pe.quantity
        if pe.ingredient.name in ingredients:
            ingredients[pe.ingredient.name]["quantity"] += quantity
        else:
            ingredients[pe.ingredient.name] = {}
            ingredients[pe.ingredient.name]["quantity"] = quantity
            ingredients[pe.ingredient.name]["unit"] = pe.ingredient.unit  # FIXME

    return JsonResponse(ingredients)


@login_required
def get_planned_recipes(request):
    grocery_list_id = request.GET.get("grocery_list")
    grocery_list = GroceryList.objects.get(id=grocery_list_id)

    planned_recipes = PlannedRecipe.objects.filter(grocery_list=grocery_list)
    planned_recipes_dict = [
        {
            "id": pr.id,
            "str": str(pr),
            "delete_url": reverse("delete_planned_recipe", args=[pr.id]),
        }
        for pr in planned_recipes
    ]
    return JsonResponse(planned_recipes_dict, safe=False)


@login_required
def get_planned_extras(request):
    grocery_list_id = request.GET.get("grocery_list")
    grocery_list = GroceryList.objects.get(id=grocery_list_id)

    planned_extras = PlannedExtra.objects.filter(grocery_list=grocery_list)
    planned_extras_dict = [
        {
            "id": pr.id,
            "str": str(pr),
            "delete_url": reverse("delete_planned_extra", args=[pr.id]),
        }
        for pr in planned_extras
    ]
    return JsonResponse(planned_extras_dict, safe=False)


@login_required
@require_http_methods(["DELETE"])
def delete_planned_recipe(request, planned_recipe_id):
    planned_recipe = get_object_or_404(PlannedRecipe, id=planned_recipe_id)
    planned_recipe.delete()
    return JsonResponse({"status": "success"}, status=200)


@login_required
@require_http_methods(["DELETE"])
def delete_planned_extra(request, planned_extra_id):
    planned_extra = get_object_or_404(PlannedExtra, id=planned_extra_id)
    planned_extra.delete()
    return JsonResponse({"status": "success"}, status=200)
