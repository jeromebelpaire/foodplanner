import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ExtrasForm, GroceryListForm, RecipeForm
from .models import GroceryList, Ingredient, PlannedExtra, PlannedRecipe, Recipe, GroceryListItem


@require_POST
def login_view(request):
    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"detail": "Successfully logged in."})
    else:
        return JsonResponse({"detail": "Invalid credentials."}, status=401)


@require_GET
@ensure_csrf_cookie
def get_csrf(request):
    token = get_token(request)
    return JsonResponse({"csrfToken": token})


@require_GET
def auth_status(request):
    if request.user.is_authenticated:
        return JsonResponse({"authenticated": True})
    else:
        return JsonResponse({"authenticated": False}, status=401)


@login_required
def home_view(request):
    recipes = Recipe.objects.order_by("-created_on")[:9]
    context = {"recipes": recipes}
    return render(request, "recipes/home.html", context)


@login_required
def get_recipes(request):
    recipes = Recipe.objects.order_by("-created_on")
    recipes_formatted = [
        {
            "title": recipe.title,
            "id": recipe.id,
            "slug": recipe.slug,
            "image": str(recipe.image),
        }
        for recipe in recipes
    ]
    return JsonResponse({"recipes": recipes_formatted})


@login_required
def get_ingredients(request):
    ingredients = Ingredient.objects.order_by("name")
    ingredients_formatted = [
        {
            # TODO check
            "title": f"{ingredient.name} ({ingredient.unit})",
            "id": ingredient.id,
        }
        for ingredient in ingredients
    ]
    return JsonResponse({"ingredients": ingredients_formatted})


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
def get_formatted_ingredients(request, recipe_id, guests=1):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe_ingredients = recipe.recipeingredient_set.all()

    scaled_ingredients = []
    for ri in recipe_ingredients:
        quantity = ri.quantity * guests
        scaled_ingredients.append(f"{ri.ingredient.name}: {quantity:.2f} {ri.ingredient.unit}")

    ingredients = {"ingredients": scaled_ingredients}

    return JsonResponse(ingredients)


@login_required
def get_recipe_info(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    ingredients = {
        "recipe": recipe.title,
        "slug": recipe.slug,
        "image": str(recipe.image),
        "instructions": recipe.content,
    }

    return JsonResponse(ingredients)


@login_required
def create_grocery_list(request):
    if request.method == "POST":
        name = request.POST.get("name")
        grocery_list = GroceryList(name=name, user=request.user)
        grocery_list.save()
        return JsonResponse(
            {
                "name": grocery_list.name,
                "id": grocery_list.id,
                "username": grocery_list.user.username,
            },
            status=201,
        )
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


def get_grocery_lists(request):
    grocery_lists_raw = GroceryList.objects.filter(user=request.user)
    grocery_lists = {
        grocery_list_raw.id: {
            "name": grocery_list_raw.name,
            "id": grocery_list_raw.id,
            "username": grocery_list_raw.user.username,
        }
        for _, grocery_list_raw in enumerate(grocery_lists_raw)
    }
    return JsonResponse(grocery_lists)


@login_required
@require_http_methods(["DELETE"])
def delete_grocery_list(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    grocery_list_id = data.get("grocery_list")
    if not grocery_list_id:
        return JsonResponse({"error": "Grocery list ID not provided"}, status=400)

    try:
        grocery_list = GroceryList.objects.filter(user=request.user).get(id=grocery_list_id)
        grocery_list.delete()
        return JsonResponse({"success": True})
    except GroceryList.DoesNotExist:
        return JsonResponse({"error": "GroceryList not found"}, status=404)


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

        for grocery_list_id, recipe_id, guests, planned_on in zip(
            data.getlist("grocery_list"),
            data.getlist("recipes"),
            data.getlist("guests"),
            data.getlist("planned_on"),
        ):
            recipe = Recipe.objects.get(pk=recipe_id)
            PlannedRecipe.objects.create(
                grocery_list_id=grocery_list_id,
                recipe=recipe,
                guests=guests,
                planned_on=planned_on if planned_on else None,
            )

        update_grocery_list_items(grocery_list_id=grocery_list_id, user=request.user)

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

        update_grocery_list_items(grocery_list_id=grocery_list_id, user=request.user)

        return JsonResponse({"success": True})


@login_required
def get_planned_ingredients(request):
    grocery_list_id = request.GET.get("grocery_list")
    grocery_list_items_object = GroceryListItem.objects.filter(grocery_list=grocery_list_id)

    grocery_list_items = {
        item.id: {
            "name": item.ingredient.name,
            "quantity": item.quantity,
            "unit": item.ingredient.unit,
            "from_recipes": item.from_recipes,
        }
        for item in grocery_list_items_object
    }

    return JsonResponse(grocery_list_items)


def update_grocery_list_items(grocery_list_id: int, user: str) -> None:
    # TODO only update changed item
    # TODO what if same ingredient, different unit?
    GroceryListItem.objects.filter(grocery_list=grocery_list_id).delete()

    grocery_list = GroceryList.objects.filter(user=user).get(id=grocery_list_id)

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
                ingredients[ri.ingredient.name]["from_recipes"] += f" & {from_recipes_text}"

            else:
                ingredients[ri.ingredient.name] = {"ingredient_id": ri.ingredient.id}
                ingredients[ri.ingredient.name]["quantity"] = quantity
                ingredients[ri.ingredient.name]["unit"] = ri.ingredient.unit
                ingredients[ri.ingredient.name]["from_recipes"] = from_recipes_text

    for pe in planned_extras:
        quantity = pe.quantity
        if pe.ingredient.name in ingredients:
            ingredients[pe.ingredient.name]["quantity"] += quantity
            ingredients[pe.ingredient.name]["from_recipes"] += f" & Extras"
        else:
            ingredients[pe.ingredient.name] = {"ingredient_id": ri.ingredient.id}
            ingredients[pe.ingredient.name]["quantity"] = quantity
            ingredients[pe.ingredient.name]["unit"] = pe.ingredient.unit
            ingredients[pe.ingredient.name]["from_recipes"] = f"Extras"

    for ingredient in ingredients.values():
        GroceryListItem.objects.create(
            grocery_list_id=grocery_list_id,
            ingredient_id=ingredient["ingredient_id"],
            from_recipes=ingredient["from_recipes"],
            quantity=ingredient["quantity"],
            is_checked=False,
        )


@login_required
def get_planned_recipes(request):
    grocery_list_id = request.GET.get("grocery_list")
    grocery_list = GroceryList.objects.filter(user=request.user).get(id=grocery_list_id)

    planned_recipes = PlannedRecipe.objects.filter(grocery_list=grocery_list).order_by("planned_on")
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
    grocery_list = GroceryList.objects.filter(user=request.user).get(id=grocery_list_id)

    planned_extras = PlannedExtra.objects.filter(grocery_list=grocery_list)
    planned_extras_dict = [
        {
            "id": pr.id,
            "str": str(pr),
            "delete_url": reverse("delete_planned_extra", args=[pr.id]),
        }
        for pr in planned_extras
    ]
    # TODO check safe=False
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
