from django.db.models import Count, Exists, OuterRef, Q
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Follow

from .models import FeedItem, FeedItemComment, FeedItemLike
from .permissions import IsOwnerOrReadOnly
from .serializers import FeedItemCommentSerializer, FeedItemSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


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
    pagination_class = StandardResultsSetPagination

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
        """
        Filter comments based on the URL kwargs.
        If 'feed_item_pk' is present (list/create via nested URL),
        filter by that feed item.
        Otherwise (detail view via /comments/pk/), return all comments,
        letting the default get_object handle filtering by pk.
        """
        queryset = FeedItemComment.objects.select_related("user")  # Base queryset

        feed_item_pk = self.kwargs.get("feed_item_pk")
        if feed_item_pk:
            # If accessed via nested URL (e.g., for list/create), filter by feed item.
            queryset = queryset.filter(feed_item_id=feed_item_pk)
        # Else: If accessed via /comments/pk/ (detail view),
        # we don't filter by feed_item here. The default get_object
        # will filter the base queryset using the comment's 'pk' from kwargs.

        return queryset

    def perform_create(self, serializer):
        """Automatically set the comment author and associate with the feed item."""
        # This action is only hit via the nested URL which guarantees feed_item_pk
        feed_item_pk = self.kwargs["feed_item_pk"]  # Can access directly now
        try:
            feed_item = FeedItem.objects.get(pk=feed_item_pk)
        except FeedItem.DoesNotExist:
            # Although the URL pattern ensures feed_item_pk is an int,
            # the FeedItem itself might not exist (e.g., deleted between requests)
            raise NotFound("Feed item not found.")
        serializer.save(user=self.request.user, feed_item=feed_item)

    # Default methods handle retrieve, update, partial_update, destroy with appropriate permissions
