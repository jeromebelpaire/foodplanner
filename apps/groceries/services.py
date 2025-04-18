from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model  # Use this to get the User model
from collections import defaultdict

# Import models using app labels to avoid potential circular imports
from .models import GroceryList, PlannedRecipe, PlannedExtra, GroceryListItem

# from apps.ingredients.models import Ingredient # Not directly needed if accessed via relations
# from apps.recipes.models import RecipeIngredient # Not directly needed

User = get_user_model()


@transaction.atomic  # Ensure the whole process is atomic
def update_grocery_list_items(grocery_list_id: int, user: User) -> None:
    """
    Recalculates and saves all GroceryListItem objects for a given grocery list
    based on its PlannedRecipe and PlannedExtra items.

    Ensures the user owns the grocery list.
    """
    try:
        # Ensure the user owns the list
        grocery_list = GroceryList.objects.get(id=grocery_list_id, user=user)
    except GroceryList.DoesNotExist:
        # Or raise PermissionDenied - depends on how you want to handle errors
        print(f"Error: GroceryList ID {grocery_list_id} not found or not owned by user {user.id}")
        return  # Exit if list not found or not owned by the user

    # Fetch related items efficiently
    planned_recipes = (
        grocery_list.plannedrecipes.select_related("recipe")
        .prefetch_related("recipe__recipeingredient_set__ingredient")
        .all()
    )
    planned_extras = grocery_list.plannedextras.select_related("ingredient").all()

    # Use defaultdict for easier aggregation
    # Key: ingredient_id, Value: {'quantity': float, 'units': set(), 'sources': list()}
    aggregated_items = defaultdict(lambda: {"quantity": 0.0, "units": set(), "sources": []})

    # --- Aggregate ingredients from planned recipes ---
    for pr in planned_recipes:
        if not pr.recipe:
            continue  # Skip if recipe is somehow missing

        source_text = f"{pr.guests}p {pr.recipe.title}"
        # Iterate through the ingredients needed for the recipe
        for ri in pr.recipe.recipeingredient_set.all():
            if not ri.ingredient:
                continue  # Skip if ingredient is somehow missing

            ingredient = ri.ingredient  # Get the related Ingredient object
            ingredient_id = ingredient.id
            quantity = ri.quantity * pr.guests

            aggregated_items[ingredient_id]["quantity"] += quantity
            aggregated_items[ingredient_id]["units"].add(ingredient.unit)
            aggregated_items[ingredient_id]["sources"].append(source_text)
            # Store ingredient object for creating GroceryListItem later
            aggregated_items[ingredient_id]["ingredient_obj"] = ingredient

    # --- Aggregate ingredients from planned extras ---
    for pe in planned_extras:
        if not pe.ingredient:
            continue  # Skip if ingredient is somehow missing

        ingredient = pe.ingredient
        ingredient_id = ingredient.id
        source_text = "Extras"

        aggregated_items[ingredient_id]["quantity"] += pe.quantity
        aggregated_items[ingredient_id]["units"].add(ingredient.unit)
        # Avoid adding "Extras" multiple times if it came from recipes too
        if source_text not in aggregated_items[ingredient_id]["sources"]:
            aggregated_items[ingredient_id]["sources"].append(source_text)
        # Store ingredient object if not already stored by a recipe
        if "ingredient_obj" not in aggregated_items[ingredient_id]:
            aggregated_items[ingredient_id]["ingredient_obj"] = ingredient

    # --- Create/Update GroceryListItem objects ---
    # Get existing items to potentially update `is_checked` status
    existing_items = {item.ingredient_id: item for item in grocery_list.grocerylistitems.all()}
    new_item_pks = set()  # Keep track of items that should exist

    items_to_create = []
    items_to_update = []

    for ingredient_id, data in aggregated_items.items():
        # Handle units - simplistic approach: join if multiple, warn if complex conversion needed
        unit_str = " & ".join(sorted(list(data["units"])))
        if len(data["units"]) > 1:
            # TODO: Implement unit conversion logic if necessary
            print(
                f"Warning: Multiple units ({unit_str}) for ingredient ID {ingredient_id} in list {grocery_list_id}. Using combined string."
            )

        # Join sources neatly
        from_recipes_str = " & ".join(sorted(list(set(data["sources"]))))

        # Check if item exists to retain its checked status
        existing_item = existing_items.get(ingredient_id)
        is_checked = existing_item.is_checked if existing_item else False

        item_data = {
            "grocery_list": grocery_list,
            "ingredient": data["ingredient_obj"],
            "quantity": round(data["quantity"], 2),  # Round to reasonable precision
            "from_recipes": from_recipes_str,
            "is_checked": is_checked,
        }

        if existing_item:
            # Update existing item if data changed (excluding is_checked initially)
            update_needed = False
            for key, value in item_data.items():
                if key != "is_checked" and getattr(existing_item, key) != value:
                    setattr(existing_item, key, value)
                    update_needed = True
            if update_needed:
                items_to_update.append(existing_item)
            new_item_pks.add(existing_item.pk)  # Mark as should exist
        else:
            # Create new item
            items_to_create.append(GroceryListItem(**item_data))
            # Note: We capture the PK after creation if needed

    # Bulk create new items
    if items_to_create:
        created_items = GroceryListItem.objects.bulk_create(items_to_create)
        for item in created_items:
            new_item_pks.add(item.pk)  # Add newly created PKs

    # Bulk update existing items (if fields changed)
    if items_to_update:
        # Specify fields to update for efficiency
        update_fields = ["quantity", "from_recipes", "updated_at"]  # Add others if needed
        GroceryListItem.objects.bulk_update(items_to_update, update_fields)

    # Delete items that are no longer needed (were in existing_items but not in aggregated_items)
    pks_to_delete = set(existing_items.keys()) - new_item_pks  # PKs to delete are ingredient IDs here, careful
    ingredient_ids_to_delete = set(existing_items.keys()) - set(aggregated_items.keys())
    if ingredient_ids_to_delete:
        GroceryListItem.objects.filter(grocery_list=grocery_list, ingredient_id__in=ingredient_ids_to_delete).delete()

    print(f"Successfully updated grocery list items for list ID: {grocery_list_id}")
