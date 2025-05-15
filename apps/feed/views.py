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
    Supports excluding specific event types via the 'exclude_event_types' query parameter
    (e.g., ?exclude_event_types=update_recipe,update_rating).
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

        excluded_types_str = self.request.query_params.get("exclude_event_types", None)
        excluded_types = []
        if excluded_types_str:
            excluded_types = [item.strip() for item in excluded_types_str.split(",") if item.strip()]
            # Optional: Validate against FeedItem.EventType.values if needed

        followed_user_ids = Follow.objects.filter(follower=user).values_list("followed_id", flat=True)

        queryset = FeedItem.objects.annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            is_liked_by_user=Exists(FeedItemLike.objects.filter(feed_item=OuterRef("pk"), user=user)),
        ).select_related(
            "user",
            "recipe__author",
            "rating__author",
            "rating__recipe",
        )

        queryset = queryset.filter(Q(user=user) | Q(user_id__in=list(followed_user_ids)))

        if excluded_types:
            queryset = queryset.exclude(event_type__in=excluded_types)

        return queryset.order_by("-created_on")


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
            return Response({"detail": "Feed item liked."}, status=status.HTTP_201_CREATED)
        else:
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
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FeedItemLike.DoesNotExist:
            raise NotFound("Like not found.")


class FeedItemCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments on feed items to be viewed, created, updated, or deleted.
    Scoped to a specific FeedItem via URL.
    """

    serializer_class = FeedItemCommentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        Filter comments based on the URL kwargs.
        If 'feed_item_pk' is present (list/create via nested URL),
        filter by that feed item.
        Otherwise (detail view via /comments/pk/), return all comments,
        letting the default get_object handle filtering by pk.
        """
        queryset = FeedItemComment.objects.select_related("user")

        feed_item_pk = self.kwargs.get("feed_item_pk")
        if feed_item_pk:
            queryset = queryset.filter(feed_item_id=feed_item_pk)

        return queryset

    def perform_create(self, serializer):
        """Automatically set the comment author and associate with the feed item."""
        # This action is only hit via the nested URL which guarantees feed_item_pk
        feed_item_pk = self.kwargs["feed_item_pk"]
        try:
            feed_item = FeedItem.objects.get(pk=feed_item_pk)
        except FeedItem.DoesNotExist:
            raise NotFound("Feed item not found.")
        serializer.save(user=self.request.user, feed_item=feed_item)
