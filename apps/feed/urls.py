from django.urls import path, include
from rest_framework.routers import SimpleRouter  # Use standard router
from .views import FeedItemViewSet, FeedItemLikeToggleView, FeedItemCommentViewSet

app_name = "feed"

# Router for FeedItems (remains the same)
router = SimpleRouter()
router.register(r"items", FeedItemViewSet, basename="feeditem")

# Manual paths for comments
comment_list = FeedItemCommentViewSet.as_view({"get": "list", "post": "create"})
comment_detail = FeedItemCommentViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    # Include the main feed item router URLs
    path("", include(router.urls)),
    # Manual URL for listing/creating comments for a specific feed item
    path("items/<int:feed_item_pk>/comments/", comment_list, name="feeditem-comment-list"),
    # Manual URL for retrieving/updating/deleting a specific comment
    # Option 1: Still nested under item (requires feed_item_pk which isn't strictly needed for lookup)
    # path('items/<int:feed_item_pk>/comments/<int:pk>/', comment_detail, name='feeditem-comment-detail'),
    # Option 2: Top-level comment endpoint (simpler lookup, less explicitly nested URL)
    path("comments/<int:pk>/", comment_detail, name="comment-detail"),  # Requires no change in viewset get_object
    # Specific URL for liking/unliking (remains the same)
    path("items/<int:pk>/like/", FeedItemLikeToggleView.as_view(), name="feeditem-like-toggle"),
]
