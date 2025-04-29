from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model  # Use this to get the User model
from collections import defaultdict

# Import models using app labels to avoid potential circular imports
from .models import GroceryList, PlannedRecipe, PlannedExtra, GroceryListItem
from apps.ingredients.models import Ingredient, IngredientUnit

# from apps.ingredients.models import Ingredient # Not directly needed if accessed via relations
# from apps.recipes.models import RecipeIngredient # Not directly needed

User = get_user_model()


@transaction.atomic  # Ensure the whole process is atomic
def update_grocery_list_items(grocery_list_id: int, user: User) -> None:
    """
    Recalculates and saves all GroceryListItem objects for a given grocery list
    based on its PlannedRecipe and PlannedExtra items. Aggregates by ingredient AND unit.

    Ensures the user owns the grocery list.
    """
    try:
        # Ensure the user owns the list
        grocery_list = GroceryList.objects.get(id=grocery_list_id, user=user)
    except GroceryList.DoesNotExist:
        # Or raise PermissionDenied - depends on how you want to handle errors
        print(f"Error: GroceryList ID {grocery_list_id} not found or not owned by user {user.id}")
        return  # Exit if list not found or not owned by the user

    # Fetch related items efficiently, including units
    planned_recipes = (
        grocery_list.plannedrecipes.select_related("recipe")
        .prefetch_related(
            "recipe__recipeingredient_set__ingredient",  # Prefetch ingredient
            "recipe__recipeingredient_set__unit",  # Prefetch unit for recipe ingredients
        )
        .all()
    )
    # Select related ingredient and unit for planned extras
    planned_extras = grocery_list.plannedextras.select_related("ingredient", "unit").all()

    # Use defaultdict for aggregation
    # Key: (ingredient_id, unit_id), Value: {'quantity': float, 'sources': list(), 'ingredient_obj': Ingredient, 'unit_obj': IngredientUnit}
    aggregated_items = defaultdict(lambda: {"quantity": 0.0, "sources": [], "ingredient_obj": None, "unit_obj": None})

    # --- Aggregate ingredients from planned recipes ---
    for pr in planned_recipes:
        if not pr.recipe:
            continue  # Skip if recipe is somehow missing

        source_text = f"{pr.guests}p {pr.recipe.title}"
        # Iterate through the ingredients needed for the recipe
        for ri in pr.recipe.recipeingredient_set.all():
            # Ensure both ingredient and unit are present
            if not ri.ingredient or not ri.unit:
                continue  # Skip if ingredient or unit is somehow missing

            ingredient = ri.ingredient
            unit = ri.unit
            agg_key = (ingredient.id, unit.id)
            quantity = ri.quantity * pr.guests

            aggregated_items[agg_key]["quantity"] += quantity
            aggregated_items[agg_key]["sources"].append(source_text)
            # Store objects only once
            if aggregated_items[agg_key]["ingredient_obj"] is None:
                aggregated_items[agg_key]["ingredient_obj"] = ingredient
                aggregated_items[agg_key]["unit_obj"] = unit

    # --- Aggregate ingredients from planned extras ---
    for pe in planned_extras:
        # Ensure both ingredient and unit are present
        if not pe.ingredient or not pe.unit:
            continue  # Skip if ingredient or unit is somehow missing

        ingredient = pe.ingredient
        unit = pe.unit
        agg_key = (ingredient.id, unit.id)
        source_text = "Extras"

        aggregated_items[agg_key]["quantity"] += pe.quantity
        if source_text not in aggregated_items[agg_key]["sources"]:
            aggregated_items[agg_key]["sources"].append(source_text)
        # Store objects if not already stored by a recipe
        if aggregated_items[agg_key]["ingredient_obj"] is None:
            aggregated_items[agg_key]["ingredient_obj"] = ingredient
            aggregated_items[agg_key]["unit_obj"] = unit

    # --- Create/Update/Delete GroceryListItem objects ---
    # Key existing items by (ingredient_id, unit_id) for quick lookup
    existing_items = {(item.ingredient_id, item.unit_id): item for item in grocery_list.grocerylistitems.all()}
    # Set of keys that should exist after aggregation
    aggregated_keys = set(aggregated_items.keys())

    items_to_create = []
    items_to_update = []

    for agg_key, data in aggregated_items.items():
        ingredient_id, unit_id = agg_key
        # Ensure we have the objects needed
        if not data["ingredient_obj"] or not data["unit_obj"]:
            print(f"Warning: Missing ingredient or unit object for key {agg_key}. Skipping.")
            continue

        # Join sources neatly
        from_recipes_str = " & ".join(sorted(list(set(data["sources"]))))

        # Check if item exists to retain its checked status
        existing_item = existing_items.get(agg_key)
        is_checked = existing_item.is_checked if existing_item else False

        item_data = {
            "grocery_list": grocery_list,
            "ingredient": data["ingredient_obj"],
            "unit": data["unit_obj"],
            "quantity": round(data["quantity"], 2),
            "from_recipes": from_recipes_str,
            "is_checked": is_checked,  # Preserve checked status
        }

        if existing_item:
            # Update existing item only if data changed (quantity or sources)
            if (
                existing_item.quantity != item_data["quantity"]
                or existing_item.from_recipes != item_data["from_recipes"]
            ):
                existing_item.quantity = item_data["quantity"]
                existing_item.from_recipes = item_data["from_recipes"]
                # Note: updated_at is handled automatically
                items_to_update.append(existing_item)
        else:
            # Create new item (without is_checked initially, handled above)
            items_to_create.append(GroceryListItem(**item_data))

    # Bulk create new items
    if items_to_create:
        GroceryListItem.objects.bulk_create(items_to_create)

    # Bulk update existing items (if fields changed)
    if items_to_update:
        GroceryListItem.objects.bulk_update(items_to_update, ["quantity", "from_recipes"])

    # --- Delete items that are no longer needed ---
    keys_to_delete = set(existing_items.keys()) - aggregated_keys
    if keys_to_delete:
        # Build a Q object to match items to delete
        # Q(ingredient_id=id1, unit_id=id1) | Q(ingredient_id=id2, unit_id=id2) ...
        delete_query = Q()
        for ing_id, unit_id in keys_to_delete:
            delete_query |= Q(ingredient_id=ing_id, unit_id=unit_id)

        if delete_query:  # Ensure the query is not empty
            GroceryListItem.objects.filter(grocery_list=grocery_list).filter(delete_query).delete()

    print(f"Successfully updated grocery list items for list ID: {grocery_list_id}")
