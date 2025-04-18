# apps/ingredients/migrations/000X_migrate_ingredient_data.py

from django.db import migrations


def forwards_func(apps, schema_editor):
    """
    Copies Ingredient data from the old 'recipes.Ingredient' model
    to the new 'ingredients.Ingredient' model.
    Preserves original IDs.
    """
    # Get the historical versions of the models
    # IMPORTANT: Use apps.get_model to get the models as they existed at this
    # point in migration history, NOT direct import.
    try:
        OldIngredient = apps.get_model("recipes", "Ingredient")
    except LookupError:
        # If the old app/model doesn't exist in the project state anymore
        # (e.g., migrations already faked/applied), skip the migration.
        print("Skipping ingredient data migration: Old model 'recipes.Ingredient' not found.")
        return

    NewIngredient = apps.get_model("ingredients", "Ingredient")
    db_alias = schema_editor.connection.alias  # Needed for multi-db support

    # Fetch all old ingredients
    old_ingredients = OldIngredient.objects.using(db_alias).all()

    new_ingredients_to_create = []
    for old_ing in old_ingredients:
        new_ingredients_to_create.append(
            NewIngredient(
                # IMPORTANT: Explicitly set the id to preserve it
                id=old_ing.id,
                name=old_ing.name,
                unit=old_ing.unit,
                # Map any other relevant fields here
                # e.g., category=old_ing.category, if it existed
            )
        )

    # Use bulk_create for efficiency
    if new_ingredients_to_create:
        NewIngredient.objects.using(db_alias).bulk_create(new_ingredients_to_create)
        print(f"\nMigrated {len(new_ingredients_to_create)} ingredients from 'recipes' to 'ingredients'.")
    else:
        print("\nNo old ingredients found to migrate.")


def backwards_func(apps, schema_editor):
    """
    Deletes the ingredients that were potentially created by the forwards pass.
    NOTE: This is a simple reversal. It doesn't move data back.
    """
    NewIngredient = apps.get_model("ingredients", "Ingredient")
    db_alias = schema_editor.connection.alias

    # A simple approach: Delete all ingredients in the new table.
    # Be CAREFUL if ingredients could have been added manually after this migration.
    # A safer approach might be to only delete based on preserved IDs, but
    # deleting all is often sufficient for reversing this specific copy operation.
    count, _ = NewIngredient.objects.using(db_alias).all().delete()
    if count:
        print(f"\nDeleted {count} ingredients from 'ingredients.Ingredient' during reversal.")


class Migration(migrations.Migration):

    # Add dependency on the previous migration in the 'ingredients' app
    # (the one that created the Ingredient model table).
    # Replace '0001_initial' with the actual name of that migration file.
    dependencies = [
        ("ingredients", "0001_refactor_folder_structure"),
        # You might also need a dependency on the LAST migration of the OLD 'recipes' app
        # if it still exists in the history, to ensure the old data is accessible.
        # ('recipes', 'XXXX_last_recipes_migration'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_code=backwards_func),
    ]
