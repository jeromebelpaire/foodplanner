from rest_framework import serializers
from .models import FeedItem, FeedItemComment, FeedItemLike

from apps.recipes.serializers import SimpleRecipeSerializer, RecipeRatingSerializer


class FeedItemCommentSerializer(serializers.ModelSerializer):
    """Serializer for FeedItemComment."""

    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = FeedItemComment
        fields = [
            "id",
            "feed_item",
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
    recipe = SimpleRecipeSerializer(read_only=True)
    rating = RecipeRatingSerializer(read_only=True)

    like_count = serializers.IntegerField(read_only=True)
    is_liked_by_user = serializers.BooleanField(read_only=True)

    comment_count = serializers.SerializerMethodField()

    class Meta:
        # TODO limit the number of fields returned for efficiency
        model = FeedItem
        fields = [
            "id",
            "user_username",
            "event_type",
            "created_on",
            "recipe",
            "rating",
            "like_count",
            "is_liked_by_user",
            "comment_count",
        ]
        read_only_fields = ["created_on", "user_username", "recipe", "rating", "like_count", "is_liked_by_user"]

    def get_comment_count(self, obj):
        """Calculates the comment count. Assumes related 'comments' are prefetched if nested."""
        if hasattr(obj, "comments"):
            return obj.comments.count()
        return getattr(obj, "comment_count", 0)
