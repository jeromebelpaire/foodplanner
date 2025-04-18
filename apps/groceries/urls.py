from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"lists", views.GroceryListViewSet, basename="grocerylist")
# Register viewsets that are typically filtered by query params
router.register(r"planned-recipes", views.PlannedRecipeViewSet, basename="plannedrecipe")
router.register(r"planned-extras", views.PlannedExtraViewSet, basename="plannedextra")
router.register(r"items", views.GroceryListItemViewSet, basename="grocerylistitem")

urlpatterns = [
    path("", include(router.urls)),
]
# Example URLs generated:
# /api/groceries/lists/
# /api/groceries/lists/{pk}/
# /api/groceries/planned-recipes/?grocery_list={list_pk}
# /api/groceries/planned-extras/?grocery_list={list_pk}
# /api/groceries/items/?grocery_list={list_pk}
# /api/groceries/items/{item_pk}/ (for PATCH)
