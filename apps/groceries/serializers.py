from rest_framework import serializers
from .models import GroceryList, PlannedRecipe, PlannedExtra, GroceryListItem

from apps.ingredients.models import Ingredient, IngredientUnit
from apps.recipes.models import Recipe

from apps.ingredients.serializers import IngredientSerializer, IngredientUnitSerializer
from apps.recipes.serializers import SimpleRecipeSerializer


class GroceryListSerializer(serializers.ModelSerializer):
    """Serializer for GroceryList"""

    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GroceryList
        fields = [
            "id",
            "name",
            "user_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_username", "created_at", "updated_at"]


class PlannedRecipeSerializer(serializers.ModelSerializer):
    """Serializer for PlannedRecipe"""

    recipe = SimpleRecipeSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all(), source="recipe", write_only=True)
    grocery_list_id = serializers.PrimaryKeyRelatedField(
        queryset=GroceryList.objects.all(), source="grocery_list", write_only=True
    )
    grocery_list_id = serializers.PrimaryKeyRelatedField(
        queryset=GroceryList.objects.all(), source="grocery_list", write_only=True
    )
    grocery_list_name = serializers.CharField(source="grocery_list.name", read_only=True)

    class Meta:
        model = PlannedRecipe
        fields = [
            "id",
            "grocery_list_id",
            "grocery_list_name",
            "recipe",
            "recipe_id",
            "guests",
            "planned_on",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "recipe", "grocery_list_name"]


class PlannedExtraSerializer(serializers.ModelSerializer):
    """Serializer for PlannedExtra"""

    ingredient = IngredientSerializer(read_only=True)
    unit = IngredientUnitSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient", write_only=True
    )
    unit_id = serializers.PrimaryKeyRelatedField(queryset=IngredientUnit.objects.all(), source="unit", write_only=True)
    grocery_list_id = serializers.PrimaryKeyRelatedField(
        queryset=GroceryList.objects.all(), source="grocery_list", write_only=True
    )
    grocery_list_name = serializers.CharField(source="grocery_list.name", read_only=True)

    class Meta:
        model = PlannedExtra
        fields = [
            "id",
            "grocery_list_id",
            "grocery_list_name",
            "ingredient",
            "ingredient_id",
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

    ingredient = IngredientSerializer(read_only=True)
    unit = IngredientUnitSerializer(read_only=True)
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
            "is_checked",
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
        ]
