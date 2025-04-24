from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication
from .models import FeedItem
from .serializers import FeedItemSerializer

# Create your views here.


class FeedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows feed items to be viewed.
    It's read-only for now.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FeedItemSerializer

    def get_queryset(self):
        """
        Return all feed items, ordered by creation date.
        Efficiently fetches related user, recipe (with author), and rating (with author and recipe)
        data for nested serialization.
        Future: Implement following logic here.
        """
        # TODO: Implement following logic
        # user = self.request.user
        # For now, return all items
        queryset = FeedItem.objects.select_related(
            "user",
            "recipe__author",  # For nested SimpleRecipeSerializer
            "rating__author",  # For nested SimpleRecipeRatingSerializerForFeed
            "rating__recipe",  # For nested SimpleRecipeRatingSerializerForFeed (recipe_title)
        ).all()

        return queryset.order_by("-created_on")
        # Later, filter based on users `user` follows
        # followed_users = user.following.all() # Assuming a following relationship exists
        # queryset = queryset.filter(user__in=followed_users)
        # return queryset
