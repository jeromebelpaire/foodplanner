from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication
from django.db.models import Q  # Import Q for complex lookups
from apps.core.models import Follow  # Import Follow model
from .models import FeedItem
from .serializers import FeedItemSerializer

# Create your views here.


class FeedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows feed items to be viewed.
    Filters items to show those from the current user and users they follow.
    It's read-only for now.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FeedItemSerializer

    def get_queryset(self):
        """
        Return feed items for the current user and users they follow,
        ordered by creation date.
        Efficiently fetches related data for nested serialization.
        """
        user = self.request.user

        # Get IDs of users the current user is following
        # We use values_list('followed_id', flat=True) for efficiency
        followed_user_ids = Follow.objects.filter(follower=user).values_list("followed_id", flat=True)

        # Base queryset with necessary select_related for performance
        queryset = FeedItem.objects.select_related(
            "user",
            "recipe__author",
            "rating__author",
            "rating__recipe",
        )

        # Filter: Include items from the current user OR from followed users
        queryset = queryset.filter(
            Q(user=user) | Q(user_id__in=list(followed_user_ids))  # Use user_id__in for efficiency
        )

        # Order by creation date, newest first
        return queryset.order_by("-created_on")
