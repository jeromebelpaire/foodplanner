from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r"recipes", api_views.RecipeViewSet, basename="recipe")
router.register(r"ingredients", api_views.IngredientViewSet, basename="ingredient")
router.register(r"grocerylists", api_views.GroceryListViewSet, basename="grocerylist")
router.register(r"plannedrecipes", api_views.PlannedRecipeViewSet, basename="plannedrecipe")
router.register(r"plannedextras", api_views.PlannedExtraViewSet, basename="plannedextra")
router.register(r"grocerylistitems", api_views.GroceryListItemViewSet, basename="grocerylistitem")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/csrf/", api_views.CsrfTokenView.as_view(), name="auth-csrf"),
    path("auth/status/", api_views.AuthStatusView.as_view(), name="auth-status"),
]
