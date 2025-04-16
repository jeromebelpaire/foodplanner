from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import (
    Recipe,
    Ingredient,
    GroceryList,
    PlannedRecipe,
    PlannedExtra,
    GroceryListItem,
    RecipeIngredient,
)
from .serializers import (
    SimpleRecipeSerializer,
    RecipeDetailSerializer,
    IngredientSerializer,
    GroceryListSerializer,
    PlannedRecipeSerializer,
    PlannedExtraSerializer,
    GroceryListItemSerializer,
)

# Using SessionAuthentication (adjust if using TokenAuthentication)
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

# --- Authentication Views ---

# If using Session Auth, you might keep simple views or integrate with dj-rest-auth/djoser


class CsrfTokenView(APIView):
    """Provides the CSRF token (if using SessionAuthentication)."""

    authentication_classes = []  # No auth needed to get CSRF token
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        from django.middleware.csrf import get_token

        token = get_token(request)
        return Response({"csrfToken": token})


class AuthStatusView(APIView):
    """Checks authentication status."""

    # Use default auth (SessionAuthentication or TokenAuthentication as configured)
    permission_classes = [permissions.AllowAny]  # Allow anyone to check, response differs

    def get(self, request, format=None):
        authenticated = request.user.is_authenticated
        # Consider returning minimal user details if authenticated
        # serializer = UserSerializer(request.user)
        # return Response({'authenticated': authenticated, 'user': serializer.data if authenticated else None})
        return Response({"authenticated": authenticated})


# Consider dj-rest-auth or djoser for login/logout views


# --- Model Views ---


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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing ingredients.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Ingredient.objects.order_by("name")
    serializer_class = IngredientSerializer
    # Add pagination for potentially long lists
    # pagination_class = YourPaginationClass


class GroceryListViewSet(viewsets.ModelViewSet):
    """
    API endpoint for grocery lists (CRUD).
    """

    serializer_class = GroceryListSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Ensure users only see their own grocery lists."""
        return GroceryList.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        """Associate the grocery list with the current user."""
        serializer.save(user=self.request.user)


# --- Views for items related to a Grocery List ---
# Option 1: Nested Routers (e.g., /api/grocerylists/1/plannedrecipes/)
# Option 2: Filtered ViewSets (e.g., /api/plannedrecipes/?grocery_list=1) - Often simpler


class PlannedRecipeViewSet(viewsets.ModelViewSet):
    serializer_class = PlannedRecipeSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by grocery list ID from query params and user."""
        queryset = PlannedRecipe.objects.filter(grocery_list__user=self.request.user)
        grocery_list_id = self.request.query_params.get("grocery_list")
        if grocery_list_id:
            queryset = queryset.filter(grocery_list_id=grocery_list_id)
        return queryset.order_by("planned_on", "created_at")  # Added created_at for stable sort

    def perform_create(self, serializer):
        # Validate that the grocery_list belongs to the request.user
        grocery_list = serializer.validated_data["grocery_list"]
        if grocery_list.user != self.request.user:
            raise PermissionDenied("You do not own this grocery list.")

        instance = serializer.save()
        # Trigger update logic after saving
        update_grocery_list_items(grocery_list_id=instance.grocery_list.id, user=self.request.user)

    def perform_destroy(self, instance):
        # Ensure the user owns the grocery list associated with the item being deleted
        if instance.grocery_list.user != self.request.user:
            raise PermissionDenied("You cannot delete items from a grocery list you do not own.")
        grocery_list_id = instance.grocery_list.id
        instance.delete()
        # Trigger update logic after deleting
        update_grocery_list_items(grocery_list_id=grocery_list_id, user=self.request.user)


class PlannedExtraViewSet(viewsets.ModelViewSet):
    serializer_class = PlannedExtraSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by grocery list ID from query params and user."""
        queryset = PlannedExtra.objects.filter(grocery_list__user=self.request.user)
        grocery_list_id = self.request.query_params.get("grocery_list")
        if grocery_list_id:
            queryset = queryset.filter(grocery_list_id=grocery_list_id)
        return queryset.order_by("created_at")

    def perform_create(self, serializer):
        # Validate that the grocery_list belongs to the request.user
        grocery_list = serializer.validated_data["grocery_list"]
        if grocery_list.user != self.request.user:
            raise PermissionDenied("You do not own this grocery list.")
        instance = serializer.save()
        update_grocery_list_items(grocery_list_id=instance.grocery_list.id, user=self.request.user)

    def perform_destroy(self, instance):
        # Ensure the user owns the grocery list associated with the item being deleted
        if instance.grocery_list.user != self.request.user:
            raise PermissionDenied("You cannot delete items from a grocery list you do not own.")
        grocery_list_id = instance.grocery_list.id
        instance.delete()
        update_grocery_list_items(grocery_list_id=grocery_list_id, user=self.request.user)


class GroceryListItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Grocery List Items. Primarily for listing and updating 'is_checked'.
    """

    serializer_class = GroceryListItemSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]  # Allow GET and PATCH (for is_checked)

    def get_queryset(self):
        """Filter by grocery list ID from query params and user."""
        queryset = GroceryListItem.objects.filter(grocery_list__user=self.request.user)
        grocery_list_id = self.request.query_params.get("grocery_list")
        if grocery_list_id:
            queryset = queryset.filter(grocery_list_id=grocery_list_id)
        # You might want specific ordering, e.g., by ingredient name
        return queryset.order_by("ingredient__name")

    # PATCH method is handled automatically by ModelViewSet for partial updates
    # Ensure your serializer allows 'is_checked' to be written.
    def perform_update(self, serializer):
        # Ensure the user owns the grocery list associated with the item being updated
        # Get the instance being updated
        instance = self.get_object()
        if instance.grocery_list.user != self.request.user:
            raise PermissionDenied("You cannot update items from a grocery list you do not own.")
        serializer.save()


# --- Helper Function (Keep or move?) ---
# This function is complex. It might be better suited as a method on the GroceryList model
# or a separate service function. Triggering it from perform_create/perform_destroy
# in PlannedRecipe/PlannedExtra ViewSets is a good approach.
def update_grocery_list_items(grocery_list_id: int, user: User) -> None:
    """
    Recalculates and saves all GroceryListItem objects for a given grocery list
    based on the associated PlannedRecipe and PlannedExtra items.
    """
    # Ensure we have the correct user object and they own the list
    grocery_list = get_object_or_404(GroceryList, id=grocery_list_id, user=user)

    # Clear existing items for this list
    GroceryListItem.objects.filter(grocery_list=grocery_list).delete()

    planned_recipes = PlannedRecipe.objects.filter(grocery_list=grocery_list)
    planned_extras = PlannedExtra.objects.filter(grocery_list=grocery_list)
    ingredients = {}  # Key: ingredient ID, Value: dict with details

    # Aggregate ingredients from planned recipes
    for planned_recipe in planned_recipes:
        from_recipes_text = f"{planned_recipe.guests}p {planned_recipe.recipe.title}"
        # Use RecipeIngredient through Recipe model
        for ri in planned_recipe.recipe.recipeingredient_set.all():
            quantity = ri.quantity * planned_recipe.guests
            ingredient_id = ri.ingredient.id

            if ingredient_id in ingredients:
                # TODO: Handle unit conversions if units differ? Assume same unit for now.
                ingredients[ingredient_id]["quantity"] += quantity
                ingredients[ingredient_id]["from_recipes"].append(from_recipes_text)
            else:
                ingredients[ingredient_id] = {
                    "ingredient_obj": ri.ingredient,  # Store the object for later use
                    "quantity": quantity,
                    "from_recipes": [from_recipes_text],  # Store as list
                }

    # Aggregate ingredients from planned extras
    for pe in planned_extras:
        ingredient_id = pe.ingredient.id
        from_recipes_text = "Extras"

        if ingredient_id in ingredients:
            # TODO: Handle unit conversions if units differ? Assume same unit for now.
            ingredients[ingredient_id]["quantity"] += pe.quantity
            if from_recipes_text not in ingredients[ingredient_id]["from_recipes"]:
                ingredients[ingredient_id]["from_recipes"].append(from_recipes_text)
        else:
            ingredients[ingredient_id] = {
                "ingredient_obj": pe.ingredient,
                "quantity": pe.quantity,
                "from_recipes": [from_recipes_text],
            }

    # Create new GroceryListItem objects
    for ingredient_id, data in ingredients.items():
        GroceryListItem.objects.create(
            grocery_list=grocery_list,
            ingredient=data["ingredient_obj"],
            # Join the list of sources with ' & '
            from_recipes=" & ".join(sorted(list(set(data["from_recipes"])))),
            quantity=data["quantity"],
            is_checked=False,  # Default to unchecked
        )
