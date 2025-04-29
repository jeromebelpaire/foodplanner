from rest_framework import serializers
from .models import GroceryList, PlannedRecipe, PlannedExtra, GroceryListItem

from apps.ingredients.models import Ingredient, IngredientUnit
from apps.recipes.models import Recipe

from apps.ingredients.serializers import IngredientSerializer, IngredientUnitSerializer
from apps.recipes.serializers import SimpleRecipeSerializer


class GroceryListSerializer(serializers.ModelSerializer):
    """Serializer for GroceryList"""

    # Display username read-only, user field itself is hidden (set in view)
    user_username = serializers.CharField(source="user.username", read_only=True)
    # Optional: More detailed user info
    # user = BasicUserSerializer(read_only=True)

    class Meta:
        model = GroceryList
        fields = [
            "id",
            "name",
            "user_username",  # Or 'user' if using nested serializer
            "created_at",
            "updated_at",
            # Consider adding counts of items? -> Usually done via separate endpoint or calculated field
        ]
        read_only_fields = ["id", "user_username", "created_at", "updated_at"]


class PlannedRecipeSerializer(serializers.ModelSerializer):
    """Serializer for PlannedRecipe"""

    # On read, show nested simple recipe details
    recipe = SimpleRecipeSerializer(read_only=True)
    # On write, accept recipe ID
    recipe_id = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all(), source="recipe", write_only=True)
    # We assume grocery_list is validated and set in the view or based on URL context
    # If it needs to be set via payload:
    grocery_list_id = serializers.PrimaryKeyRelatedField(
        queryset=GroceryList.objects.all(), source="grocery_list", write_only=True
    )
    # You might want to show the list name on read?
    grocery_list_name = serializers.CharField(source="grocery_list.name", read_only=True)

    class Meta:
        model = PlannedRecipe
        fields = [
            "id",
            "grocery_list_id",  # Write-only ID for association
            "grocery_list_name",  # Read-only name for context
            "recipe",  # Read-only nested recipe details
            "recipe_id",  # Write-only ID for recipe association
            "guests",
            "planned_on",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "recipe", "grocery_list_name"]
        # Note: grocery_list_id is write_only, recipe_id is write_only


class PlannedExtraSerializer(serializers.ModelSerializer):
    """Serializer for PlannedExtra"""

    # On read, show nested ingredient details
    ingredient = IngredientSerializer(read_only=True)
    unit = IngredientUnitSerializer(read_only=True)
    # On write, accept ingredient ID
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient", write_only=True
    )
    unit_id = serializers.PrimaryKeyRelatedField(queryset=IngredientUnit.objects.all(), source="unit", write_only=True)
    # Grocery list association (similar to PlannedRecipeSerializer)
    grocery_list_id = serializers.PrimaryKeyRelatedField(
        queryset=GroceryList.objects.all(), source="grocery_list", write_only=True
    )
    grocery_list_name = serializers.CharField(source="grocery_list.name", read_only=True)

    class Meta:
        model = PlannedExtra
        fields = [
            "id",
            "grocery_list_id",  # Write-only
            "grocery_list_name",  # Read-only
            "ingredient",  # Read-only nested details
            "ingredient_id",  # Write-only
            "quantity",
            "unit",
            "unit_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "ingredient", "grocery_list_name"]


class GroceryListItemSerializer(serializers.ModelSerializer):
    """
    Serializer for GroceryListItem.
    Primarily used for reading the generated list and updating 'is_checked'.
    """

    # Show nested ingredient details
    ingredient = IngredientSerializer(read_only=True)
    unit = IngredientUnitSerializer(read_only=True)
    # Grocery list association - usually known from context, but included for completeness
    grocery_list_id = serializers.IntegerField(source="grocery_list.id", read_only=True)
    grocery_list_name = serializers.CharField(source="grocery_list.name", read_only=True)

    class Meta:
        model = GroceryListItem
        fields = [
            "id",
            "grocery_list_id",
            "grocery_list_name",
            "ingredient",
            "unit",
            "from_recipes",
            "quantity",
            "is_checked",  # This field should be writable (for PATCH requests)
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "grocery_list_id",
            "grocery_list_name",
            "ingredient",
            "unit",
            "from_recipes",
            "quantity",
            "updated_at",
            # Note: 'is_checked' is intentionally NOT read-only
        ]
