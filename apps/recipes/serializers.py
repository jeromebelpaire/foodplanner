from rest_framework import serializers
from .models import Recipe, Ingredient, GroceryList, PlannedRecipe, PlannedExtra, GroceryListItem, RecipeIngredient
from django.contrib.auth.models import User


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "unit"]  # Or '__all__'


class SimpleRecipeSerializer(serializers.ModelSerializer):
    # Use a simpler serializer for lists where full detail isn't needed
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ["id", "title", "slug", "image"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    # If needed for recipe details
    name = serializers.CharField(source="ingredient.name")
    unit = serializers.CharField(source="ingredient.unit")

    class Meta:
        model = RecipeIngredient
        fields = ["name", "unit", "quantity"]  # quantity is per person


class RecipeDetailSerializer(serializers.ModelSerializer):
    # More detailed serializer for retrieving a single recipe
    ingredients = RecipeIngredientSerializer(source="recipeingredient_set", many=True, read_only=True)
    author_username = serializers.CharField(source="author.username", read_only=True)
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "slug",
            "author_username",
            "content",
            "created_on",
            "updated_on",
            "image",
            "ingredients",
        ]


class GroceryListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    # Mark user as read-only; it will be set automatically based on the request user
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = GroceryList
        fields = ["id", "name", "user", "username", "created_at", "updated_at"]


class PlannedRecipeSerializer(serializers.ModelSerializer):
    recipe_title = serializers.CharField(source="recipe.title", read_only=True)
    # You might want related fields like grocery_list and recipe to be writeable using their IDs
    # recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    # grocery_list = serializers.PrimaryKeyRelatedField(queryset=GroceryList.objects.all()) # Filter this in the view

    class Meta:
        model = PlannedRecipe
        # Adjust fields based on what the frontend needs to send/receive
        fields = ["id", "grocery_list", "recipe", "recipe_title", "guests", "planned_on", "created_at"]
        read_only_fields = ["created_at"]  # Fields that shouldn't be modified directly via API


class PlannedExtraSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    ingredient_unit = serializers.CharField(source="ingredient.unit", read_only=True)

    class Meta:
        model = PlannedExtra
        fields = ["id", "grocery_list", "ingredient", "ingredient_name", "ingredient_unit", "quantity", "created_at"]
        read_only_fields = ["created_at"]


class GroceryListItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="ingredient.name", read_only=True)
    unit = serializers.CharField(source="ingredient.unit", read_only=True)

    class Meta:
        model = GroceryListItem
        fields = [
            "id",
            "grocery_list",
            "ingredient",
            "name",
            "unit",
            "quantity",
            "from_recipes",
            "is_checked",
            "updated_at",
        ]
        read_only_fields = [
            "grocery_list",
            "ingredient",
            "name",
            "unit",
            "quantity",
            "from_recipes",
            "updated_at",
        ]  # Only allow updating is_checked


# Add User serializer if needed, e.g., for auth status
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "is_authenticated"]  # Add other fields if necessary
