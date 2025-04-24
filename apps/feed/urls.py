from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedItemViewSet

router = DefaultRouter()
router.register(r"feed", FeedItemViewSet, basename="feed")

urlpatterns = [
    path("", include(router.urls)),
]
