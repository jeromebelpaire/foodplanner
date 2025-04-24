from rest_framework import serializers
from .models import FeedItem

# Import serializers for nesting
from apps.recipes.serializers import SimpleRecipeSerializer, RecipeRatingSerializer


# A simplified RecipeRatingSerializer for nesting inside FeedItem
class SimpleRecipeRatingSerializerForFeed(serializers.ModelSerializer):
    # We only need a few fields for the feed display
    author_username = serializers.CharField(source="author.username", read_only=True)
    recipe_title = serializers.CharField(source="recipe.title", read_only=True)
    # Convert 0-10 rating to 0-5 stars for display?
    rating_stars = serializers.SerializerMethodField()

    class Meta:
        model = RecipeRatingSerializer.Meta.model  # Use the actual RecipeRating model
        fields = [
            "id",
            "author_username",
            "recipe_title",
            "rating",  # Keep the original 0-10 rating
            "rating_stars",  # Add the 0-5 representation
            "comment",
            "created_on",
        ]

    def get_rating_stars(self, obj):
        # Convert 0-10 scale to 0-5
        return obj.rating / 2 if obj.rating is not None else None


class FeedItemSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    # Nest the full SimpleRecipeSerializer when the item is a recipe
    recipe = SimpleRecipeSerializer(read_only=True)
    # Nest the simplified rating serializer when the item is a rating
    rating = SimpleRecipeRatingSerializerForFeed(read_only=True)

    class Meta:
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
