from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"lists", views.GroceryListViewSet, basename="grocerylist")
router.register(r"planned-recipes", views.PlannedRecipeViewSet, basename="plannedrecipe")
router.register(r"planned-extras", views.PlannedExtraViewSet, basename="plannedextra")
router.register(r"items", views.GroceryListItemViewSet, basename="grocerylistitem")

urlpatterns = [
    path("", include(router.urls)),
]
