from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Recipe
from .serializers import RecipeDetailSerializer, SimpleRecipeSerializer

from apps.core.views import IsAuthorOrSuperuser


class RecipeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recipes to be viewed, created, updated and deleted.
    Regular users can only modify their own recipes, superusers can modify any.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, IsAuthorOrSuperuser]

    def get_queryset(self):
        # For list and retrieve actions, show all recipes
        if self.action in ["list", "retrieve", "formatted_ingredients"]:
            return Recipe.objects.all().order_by("-created_on")

        if self.request.user.is_superuser:
            return Recipe.objects.all().order_by("-created_on")

        else:
            return Recipe.objects.filter(author=self.request.user).order_by("-created_on")

    def get_serializer_class(self):
        if self.action == "list":
            return SimpleRecipeSerializer
        return RecipeDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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
