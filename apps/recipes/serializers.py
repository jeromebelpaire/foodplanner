from django.utils.text import slugify
from rest_framework import serializers

from apps.ingredients.serializers import IngredientSerializer

from .models import Recipe, RecipeIngredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    # Include ingredient details directly using IngredientSerializer
    # Use source='ingredient' to specify the related field name
    ingredient = IngredientSerializer(read_only=True)
    # You might want to allow writing ingredient by ID
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=IngredientSerializer.Meta.model.objects.all(),
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


class SimpleRecipeSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Recipe
        fields = ["id", "title", "slug", "author_username", "created_on", "image"]
        read_only_fields = ["slug", "author_username", "created_on"]


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

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipeingredient_set", [])
        validated_data["slug"] = slugify(validated_data["title"])
        if "author" not in validated_data:
            validated_data["author"] = self.context["request"].user

        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipeingredient_set", [])

        # Update recipe fields
        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        instance.image = validated_data.get("image", instance.image)
        # Update slug only if title changed
        if "title" in validated_data:
            instance.slug = slugify(validated_data["title"])
        instance.save()

        # Handle ingredients update - clear existing and create new ones
        # TODO: A more sophisticated approach would update existing ingredients
        if ingredients_data:
            instance.recipeingredient_set.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(recipe=instance, **ingredient_data)

        return instance
