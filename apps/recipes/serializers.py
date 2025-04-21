import json

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
    recipe_ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source="recipeingredient_set",  # TODO review
    )  # Read-only nested for now

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
        # Get the raw JSON string from the input data if present for create
        ingredients_json = self.initial_data.get("recipe_ingredients")
        ingredients_data = None
        if ingredients_json:
            try:
                ingredients_data = json.loads(ingredients_json)
                if not isinstance(ingredients_data, list):
                    raise serializers.ValidationError("recipe_ingredients must be a list.")
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for recipe_ingredients.")

        # Create the recipe instance
        validated_data["slug"] = slugify(validated_data["title"])
        if "author" not in validated_data and "request" in self.context:
            validated_data["author"] = self.context["request"].user
        # Ensure 'recipe_ingredients' (the serializer field) is not passed to Recipe.objects.create
        validated_data.pop("recipe_ingredients", None)  # Remove if present from read operation leftovers
        validated_data.pop("recipeingredient_set", None)  # Remove if present

        recipe = Recipe.objects.create(**validated_data)

        # Create ingredients if data was provided
        if ingredients_data:
            for ingredient_item in ingredients_data:
                if "ingredient_id" in ingredient_item and "quantity" in ingredient_item:
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient_id=ingredient_item["ingredient_id"],
                        quantity=ingredient_item["quantity"],
                    )
                else:
                    print(f"Skipping ingredient item during creation due to missing data: {ingredient_item}")

        return recipe

    def update(self, instance, validated_data):
        ingredients_json = self.initial_data.get("recipe_ingredients")  # Get raw data from form
        ingredients_data = None
        if ingredients_json:
            try:
                ingredients_data = json.loads(ingredients_json)
                # Basic validation: ensure it's a list
                if not isinstance(ingredients_data, list):
                    raise serializers.ValidationError("recipe_ingredients must be a list.")
                # Optional: Deeper validation of list items if needed
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for recipe_ingredients.")

        # Update recipe fields
        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        # Handle image removal/update (ensure your backend handles image field updates correctly)
        # If 'image' is not in validated_data, it means no new file was uploaded.
        # If you need to handle image *removal*, the frontend needs to send a specific signal
        # (like `image=null` or an empty string) and the backend needs to interpret it.
        # For now, we assume validated_data handles new uploads correctly.
        instance.image = validated_data.get("image", instance.image)  # TODO Check if this logic is sufficient
        # Update slug only if title changed
        if "title" in validated_data:
            instance.slug = slugify(validated_data["title"])
        instance.save()

        # Handle ingredients update using the parsed data
        if ingredients_data is not None:  # Process if data was provided and parsed
            instance.recipeingredient_set.all().delete()  # Clear existing
            for ingredient_item in ingredients_data:
                # Ensure required fields are present in each item
                if "ingredient_id" in ingredient_item and "quantity" in ingredient_item:
                    RecipeIngredient.objects.create(
                        recipe=instance,
                        ingredient_id=ingredient_item["ingredient_id"],
                        quantity=ingredient_item["quantity"],
                    )
                else:
                    # Handle cases with missing data, maybe raise validation error or log warning
                    print(f"Skipping ingredient item due to missing data: {ingredient_item}")
                    # Alternatively: raise serializers.ValidationError(f"Missing data in ingredient item: {ingredient_item}")

        return instance
