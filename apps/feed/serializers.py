from rest_framework import serializers
from .models import FeedItem, FeedItemComment, FeedItemLike

from apps.recipes.serializers import SimpleRecipeSerializer, RecipeRatingSerializer


class FeedItemCommentSerializer(serializers.ModelSerializer):
    """Serializer for FeedItemComment."""

    user_username = serializers.CharField(source="user.username", read_only=True)
    # feed_item = serializers.PrimaryKeyRelatedField(read_only=True) # FK is usually set via URL

    class Meta:
        model = FeedItemComment
        fields = [
            "id",
            "feed_item",  # Keep for reference, but usually set implicitly
            "user_username",
            "text",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user_username", "created_at", "updated_at", "feed_item"]

    # If creating comments through this serializer directly (not recommended for nested viewsets),
    # you might need to override create to set user and feed_item from context.


class FeedItemSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    # Nest the full SimpleRecipeSerializer when the item is a recipe
    recipe = SimpleRecipeSerializer(read_only=True)
    # Nest the simplified rating serializer when the item is a rating
    rating = RecipeRatingSerializer(read_only=True)

    # Add fields for likes
    like_count = serializers.IntegerField(read_only=True)  # Populated by annotation in view
    is_liked_by_user = serializers.BooleanField(read_only=True)  # Populated by annotation in view

    # Add field for comments (optional: maybe just count or first few?)
    # For now, let's include a basic comment count
    comment_count = serializers.SerializerMethodField()
    # To include nested comments (use prefetch_related in view):
    # comments = FeedItemCommentSerializer(many=True, read_only=True)

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
            "like_count",  # Added
            "is_liked_by_user",  # Added
            "comment_count",  # Added (could be nested comments instead/as well)
        ]
        # Note: recipe and rating are now read-only due to nesting serializers
        read_only_fields = ["created_on", "user_username", "recipe", "rating", "like_count", "is_liked_by_user"]

    def get_comment_count(self, obj):
        """Calculates the comment count. Assumes related 'comments' are prefetched if nested."""
        # If comments are prefetched, this is efficient:
        if hasattr(obj, "comments"):
            return obj.comments.count()
        # Otherwise, query the database (less efficient if done per item)
        # return obj.comments.count()
        # For simple count, prefer annotation in the viewset like with likes.
        # If using annotation `comment_count_annotation` in view:
        # return getattr(obj, 'comment_count_annotation', 0)
        # Let's stick to the annotation approach for consistency and efficiency
        # Ensure the view annotates 'comment_count' as well.
        return getattr(obj, "comment_count", 0)
