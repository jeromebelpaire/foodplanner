from rest_framework import viewsets, permissions, status, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView  # Import APIView
from rest_framework.response import Response  # Import Response
from rest_framework.exceptions import NotFound  # Import NotFound

from django.db.models import Q, Count, Exists, OuterRef  # Import Count, Exists, OuterRef for annotations
from apps.core.models import Follow

# Import new models and serializers
from .models import FeedItem, FeedItemLike, FeedItemComment
from .serializers import FeedItemSerializer, FeedItemCommentSerializer
from .permissions import IsOwnerOrReadOnly  # Import custom permission

# Create your views here.


class FeedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows feed items to be viewed.
    Filters items to show those from the current user and users they follow.
    Includes like/comment counts and whether the current user liked the item.
    It's read-only for now.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FeedItemSerializer

    def get_queryset(self):
        """
        Return feed items for the current user and users they follow,
        ordered by creation date.
        Annotates like/comment counts and user's like status.
        Efficiently fetches related data.
        """
        user = self.request.user

        followed_user_ids = Follow.objects.filter(follower=user).values_list("followed_id", flat=True)

        # Annotate with like count, comment count, and if the current user has liked the item
        queryset = FeedItem.objects.annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),  # Add comment count annotation
            is_liked_by_user=Exists(FeedItemLike.objects.filter(feed_item=OuterRef("pk"), user=user)),
        ).select_related(
            "user",
            "recipe__author",
            "rating__author",
            "rating__recipe",
        )
        # Uncomment and add 'comments__user' if nesting comments in serializer
        # .prefetch_related('comments__user')

        # Filter: Include items from the current user OR from followed users
        queryset = queryset.filter(Q(user=user) | Q(user_id__in=list(followed_user_ids)))

        return queryset.order_by("-created_on")


# --- Like Toggle View ---


class FeedItemLikeToggleView(APIView):
    """
    API view to like (POST) or unlike (DELETE) a specific FeedItem.
    Expects the FeedItem pk in the URL.
    Requires authentication.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, format=None):
        """Like a FeedItem specified by pk."""
        try:
            feed_item = FeedItem.objects.get(pk=pk)
        except FeedItem.DoesNotExist:
            raise NotFound("Feed item not found.")

        # Use get_or_create to handle potential race conditions and prevent duplicates
        like, created = FeedItemLike.objects.get_or_create(user=request.user, feed_item=feed_item)

        if created:
            # Optionally return the updated like count or just success
            return Response({"detail": "Feed item liked."}, status=status.HTTP_201_CREATED)
        else:
            # Already liked
            return Response({"detail": "You have already liked this item."}, status=status.HTTP_200_OK)

    def delete(self, request, pk, format=None):
        """Unlike a FeedItem specified by pk."""
        try:
            feed_item = FeedItem.objects.get(pk=pk)
        except FeedItem.DoesNotExist:
            raise NotFound("Feed item not found.")

        try:
            like_instance = FeedItemLike.objects.get(user=request.user, feed_item=feed_item)
            like_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)  # Standard success for DELETE
        except FeedItemLike.DoesNotExist:
            # Can return 404 or 400 if they try to unlike something not liked
            raise NotFound("Like not found.")


# --- Comment ViewSet ---


class FeedItemCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments on feed items to be viewed, created, updated, or deleted.
    Scoped to a specific FeedItem via URL.
    """

    serializer_class = FeedItemCommentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]  # Allow read, require ownership for write

    def get_queryset(self):
        """Filter comments to only those belonging to the specified feed item."""
        feed_item_pk = self.kwargs.get("feed_item_pk")
        if not feed_item_pk:
            # This shouldn't happen with proper URL routing, but handle defensively
            return FeedItemComment.objects.none()

        # Prefetch related user for efficiency when serializing
        return FeedItemComment.objects.filter(feed_item_id=feed_item_pk).select_related("user")

    def perform_create(self, serializer):
        """Automatically set the comment author and associate with the feed item."""
        feed_item_pk = self.kwargs.get("feed_item_pk")
        try:
            feed_item = FeedItem.objects.get(pk=feed_item_pk)
        except FeedItem.DoesNotExist:
            raise NotFound("Feed item not found.")
        serializer.save(user=self.request.user, feed_item=feed_item)

    # Default methods handle retrieve, update, partial_update, destroy with appropriate permissions
