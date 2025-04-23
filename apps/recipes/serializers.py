import json
import nh3

from django.utils.text import slugify
from rest_framework import serializers

from apps.ingredients.serializers import IngredientSerializer

from .models import Recipe, RecipeIngredient, RecipeRating


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
        fields = [
            "id",
            "title",
            "slug",
            "author_username",
            "created_on",
            "image",
            "average_rating",
            "rating_count",
        ]
        read_only_fields = ["slug", "author_username", "created_on"]


class SanitizedHtmlField(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return nh3.clean(value) if value else value


class RecipeDetailSerializer(serializers.ModelSerializer):
    remove_image = serializers.BooleanField(required=False)
    author_username = serializers.CharField(source="author.username", read_only=True)
    recipe_ingredients = RecipeIngredientSerializer(
        many=True,
        source="recipeingredient_set",
        required=False,
    )
    content = SanitizedHtmlField()

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
            "average_rating",
            "rating_count",
            "remove_image",
        ]
        read_only_fields = ["slug", "author_username", "created_on", "updated_on"]

    def validate(self, data):
        # Parse and validate recipe_ingredients from initial_data (because data doesn't have it)
        # This is due to having a multipart/form-data request for the image upload
        ingredients_raw = self.initial_data.get("recipe_ingredients")
        if ingredients_raw:
            try:
                ingredients_list = json.loads(ingredients_raw)
                ingredient_serializer = RecipeIngredientSerializer(
                    data=ingredients_list, many=True, context=self.context
                )
                ingredient_serializer.is_valid(raise_exception=True)
                data["recipeingredient_set"] = ingredient_serializer.validated_data
            except json.JSONDecodeError:
                raise serializers.ValidationError({"recipe_ingredients": "Invalid JSON format"})

        return data

    def _set_author_and_slug(self, validated_data):
        """Helper to set author and slug, common for create/update."""
        if "title" in validated_data:
            validated_data["slug"] = slugify(validated_data["title"])
        if "author" not in validated_data and "request" in self.context:
            validated_data["author"] = self.context["request"].user
        return validated_data

    def create(self, validated_data):
        validated_data.pop("remove_image", None)
        ingredients = validated_data.pop("recipeingredient_set", [])
        validated_data = self._set_author_and_slug(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        for item in ingredients:
            RecipeIngredient.objects.create(recipe=recipe, **item)
        return recipe

    def update(self, instance, validated_data):
        remove_image = validated_data.pop("remove_image", False)
        if remove_image and instance.image:
            instance.image.delete(save=False)
            validated_data["image"] = None
        # let the parent handle simple fields & slug
        ingredients = validated_data.pop("recipeingredient_set", None)
        instance = super().update(instance, validated_data)
        if ingredients is not None:
            # replace all ingredients in one shot
            instance.recipeingredient_set.all().delete()
            for item in ingredients:
                RecipeIngredient.objects.create(recipe=instance, **item)
        return instance


class RecipeRatingSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    # TODO check why using username instead of id
    # Use PrimaryKeyRelatedField for writing the recipe ID
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = RecipeRating
        fields = [
            "id",
            "recipe",
            "author_username",
            "rating",
            "comment",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["author_username", "created_on", "updated_on"]
