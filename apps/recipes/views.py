from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Recipe
from .serializers import (
    SimpleRecipeSerializer,
    RecipeDetailSerializer,
)

# Using SessionAuthentication (adjust if using TokenAuthentication)
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated


class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows recipes to be viewed.
    """

    authentication_classes = [SessionAuthentication]  # Example
    permission_classes = [IsAuthenticated]  # Example: Must be logged in to view
    queryset = Recipe.objects.all().order_by("-created_on")

    def get_serializer_class(self):
        if self.action == "list":
            return SimpleRecipeSerializer  # Use simple view for list
        return RecipeDetailSerializer  # Use detailed view for retrieve

    @action(detail=True, methods=["get"])
    def formatted_ingredients(self, request, pk=None):
        """
        Returns scaled ingredients for a given recipe and number of guests.
        Example: /api/recipes/1/formatted_ingredients/?guests=4
        """
        recipe = self.get_object()
        try:
            guests = int(request.query_params.get("guests", 1))
        except ValueError:
            return Response({"error": "Invalid 'guests' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        recipe_ingredients = recipe.recipeingredient_set.all()
        scaled_ingredients = []
        for ri in recipe_ingredients:
            quantity = ri.quantity * guests
            scaled_ingredients.append(f"{ri.ingredient.name}: {quantity:.2f} {ri.ingredient.unit}")

        return Response({"ingredients": scaled_ingredients})


# # --- Helper Function (Keep or move?) ---
# # This function is complex. It might be better suited as a method on the GroceryList model
# # or a separate service function. Triggering it from perform_create/perform_destroy
# # in PlannedRecipe/PlannedExtra ViewSets is a good approach.
# def update_grocery_list_items(grocery_list_id: int, user: User) -> None:
#     """
#     Recalculates and saves all GroceryListItem objects for a given grocery list
#     based on the associated PlannedRecipe and PlannedExtra items.
#     """
#     # Ensure we have the correct user object and they own the list
#     grocery_list = get_object_or_404(GroceryList, id=grocery_list_id, user=user)

#     # Clear existing items for this list
#     GroceryListItem.objects.filter(grocery_list=grocery_list).delete()

#     planned_recipes = PlannedRecipe.objects.filter(grocery_list=grocery_list)
#     planned_extras = PlannedExtra.objects.filter(grocery_list=grocery_list)
#     ingredients = {}  # Key: ingredient ID, Value: dict with details

#     # Aggregate ingredients from planned recipes
#     for planned_recipe in planned_recipes:
#         from_recipes_text = f"{planned_recipe.guests}p {planned_recipe.recipe.title}"
#         # Use RecipeIngredient through Recipe model
#         for ri in planned_recipe.recipe.recipeingredient_set.all():
#             quantity = ri.quantity * planned_recipe.guests
#             ingredient_id = ri.ingredient.id

#             if ingredient_id in ingredients:
#                 # TODO: Handle unit conversions if units differ? Assume same unit for now.
#                 ingredients[ingredient_id]["quantity"] += quantity
#                 ingredients[ingredient_id]["from_recipes"].append(from_recipes_text)
#             else:
#                 ingredients[ingredient_id] = {
#                     "ingredient_obj": ri.ingredient,  # Store the object for later use
#                     "quantity": quantity,
#                     "from_recipes": [from_recipes_text],  # Store as list
#                 }

#     # Aggregate ingredients from planned extras
#     for pe in planned_extras:
#         ingredient_id = pe.ingredient.id
#         from_recipes_text = "Extras"

#         if ingredient_id in ingredients:
#             # TODO: Handle unit conversions if units differ? Assume same unit for now.
#             ingredients[ingredient_id]["quantity"] += pe.quantity
#             if from_recipes_text not in ingredients[ingredient_id]["from_recipes"]:
#                 ingredients[ingredient_id]["from_recipes"].append(from_recipes_text)
#         else:
#             ingredients[ingredient_id] = {
#                 "ingredient_obj": pe.ingredient,
#                 "quantity": pe.quantity,
#                 "from_recipes": [from_recipes_text],
#             }

#     # Create new GroceryListItem objects
#     for ingredient_id, data in ingredients.items():
#         GroceryListItem.objects.create(
#             grocery_list=grocery_list,
#             ingredient=data["ingredient_obj"],
#             # Join the list of sources with ' & '
#             from_recipes=" & ".join(sorted(list(set(data["from_recipes"])))),
#             quantity=data["quantity"],
#             is_checked=False,  # Default to unchecked
#         )
