from rest_framework import serializers
from .models import Ingredient, IngredientUnit


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "fdc_id"]


class IngredientUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientUnit
        fields = ["id", "name"]
