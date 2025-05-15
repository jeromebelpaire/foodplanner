from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import FeedItemViewSet, FeedItemLikeToggleView, FeedItemCommentViewSet

app_name = "feed"

router = SimpleRouter()
router.register(r"items", FeedItemViewSet, basename="feeditem")

comment_list = FeedItemCommentViewSet.as_view({"get": "list", "post": "create"})
comment_detail = FeedItemCommentViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("", include(router.urls)),
    path("items/<int:feed_item_pk>/comments/", comment_list, name="feeditem-comment-list"),
    path("comments/<int:pk>/", comment_detail, name="comment-detail"),
    path("comments/<int:pk>/", comment_detail, name="comment-detail"),
    path("items/<int:pk>/like/", FeedItemLikeToggleView.as_view(), name="feeditem-like-toggle"),
]
