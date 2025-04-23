from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"recipes", views.RecipeViewSet, basename="recipe")
router.register(r"ratings", views.RecipeRatingViewSet, basename="reciperating")

urlpatterns = [
    path("", include(router.urls)),
]
