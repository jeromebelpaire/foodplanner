from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Follow, TermsOfServiceVersion

User = get_user_model()


class UserSearchSerializer(serializers.ModelSerializer):
    """
    Serializer for user search results, showing minimal public info.
    Adds an 'is_following' field to indicate if the requesting user follows this user.
    """

    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "is_following",
        ]

    def get_is_following(self, obj):
        """Check if the current request user is following the user ('obj')."""
        request_user = self.context.get("request").user
        if request_user and request_user.is_authenticated:
            # Check if a Follow relationship exists from request_user to obj
            return Follow.objects.filter(follower=request_user, followed=obj).exists()
        return False


class TermsOfServiceVersionSerializer(serializers.ModelSerializer):
    """Serializer for public display of Terms of Service versions."""

    class Meta:
        model = TermsOfServiceVersion
        fields = [
            "version_number",
            "content",
            "published_at",
        ]
        read_only_fields = fields


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for the Follow relationship.
    Used primarily for validation when creating/destroying follows via an API endpoint.
    We don't usually need to list Follow objects directly, but handle follow/unfollow actions.
    """

    follower_username = serializers.CharField(source="follower.username", read_only=True)
    followed_username = serializers.CharField(source="followed.username", read_only=True)

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "followed",
            "created_at",
            "follower_username",
            "followed_username",
        ]
        read_only_fields = [
            "follower",
            "created_at",
            "follower_username",
            "followed_username",
        ]

    def validate(self, attrs):
        follower = self.context["request"].user
        followed = attrs.get("followed")
        if follower == followed:
            raise serializers.ValidationError("Users cannot follow themselves.")
        return attrs

    def create(self, validated_data):
        # Set the follower automatically from the request user
        validated_data["follower"] = self.context["request"].user
        # Use get_or_create to handle potential race conditions or redundant requests gracefully
        # Although the view logic might already prevent duplicates
        follow, created = Follow.objects.get_or_create(**validated_data)
        return follow
