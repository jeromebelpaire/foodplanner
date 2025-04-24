from rest_framework import serializers
from .models import FeedItem

from apps.recipes.serializers import SimpleRecipeSerializer, RecipeRatingSerializer


class FeedItemSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    # Nest the full SimpleRecipeSerializer when the item is a recipe
    recipe = SimpleRecipeSerializer(read_only=True)
    # Nest the simplified rating serializer when the item is a rating
    rating = RecipeRatingSerializer(read_only=True)

    class Meta:
        # TODO limit the number of fields returned for efficiency
        model = FeedItem
        fields = [
            "id",
            "user_username",
            "event_type",
            "created_on",
            "recipe",  # Will be a nested object or null
            "rating",  # Will be a nested object or null
        ]
        # Note: recipe and rating are now read-only due to nesting serializers
        read_only_fields = ["created_on", "user_username", "recipe", "rating"]
