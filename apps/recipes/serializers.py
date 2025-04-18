# apps/recipes/serializers.py
from rest_framework import serializers

# IMPORTANT: Import IngredientSerializer from the ingredients app
from apps.ingredients.serializers import IngredientSerializer
from .models import Recipe, RecipeIngredient


# Serializer for the through model, used in RecipeDetailSerializer
class RecipeIngredientSerializer(serializers.ModelSerializer):
    # Include ingredient details directly using IngredientSerializer
    # Use source='ingredient' to specify the related field name
    ingredient = IngredientSerializer(read_only=True)
    # You might want to allow writing ingredient by ID
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=IngredientSerializer.Meta.model.objects.all(),  # Queryset from Ingredient model
        source="ingredient",
        write_only=True,
    )
    unit = serializers.CharField(source="ingredient.unit", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = [
            "id",
            "ingredient_id",
            "ingredient",
            "name",
            "quantity",
            "unit",
        ]  #'ingredient' for reading, 'ingredient_id' for writing


# Basic serializer for list views
class SimpleRecipeSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Recipe
        fields = ["id", "title", "slug", "author_username", "created_on", "image"]
        read_only_fields = ["slug", "author_username", "created_on"]


# Detailed serializer for retrieve view, including ingredients
class RecipeDetailSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    # Use the RecipeIngredientSerializer for the nested relationship
    # Use source='recipe_ingredients' based on the related_name in RecipeIngredient model
    recipe_ingredients = RecipeIngredientSerializer(many=True, read_only=True)  # Read-only nested for now

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
            "recipe_ingredients",
        ]
        read_only_fields = ["slug", "author_username", "created_on", "updated_on"]

    # If you want to support creating/updating recipes with ingredients in one go,
    # you'll need to implement custom .create() and .update() methods here.
    # See DRF documentation on "Writable Nested Serializers".
