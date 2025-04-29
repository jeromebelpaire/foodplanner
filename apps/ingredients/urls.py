from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngredientViewSet, IngredientUnitViewSet

router = DefaultRouter()
router.register(r"ingredients", IngredientViewSet, basename="ingredient")
router.register(r"units", IngredientUnitViewSet, basename="ingredientunit")

urlpatterns = [
    path("", include(router.urls)),
]
