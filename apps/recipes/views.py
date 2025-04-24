from rest_framework import status, viewsets, permissions, serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend  # TODO check if this is needed

from .models import Recipe, RecipeRating
from .serializers import (
    RecipeDetailSerializer,
    SimpleRecipeSerializer,
    RecipeRatingSerializer,
)
from .services import update_recipe_ratings
from .permissions import IsAuthorOrReadOnly

from apps.core.views import IsAuthorOrSuperuser
from apps.feed.models import FeedItem


class RecipeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recipes to be viewed, created, updated and deleted.
    Regular users can only modify their own recipes, superusers can modify any.
    Use ?mine=true to filter for the logged-in user's recipes.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, IsAuthorOrSuperuser]
    # queryset = (
    #     Recipe.objects.select_related("author")
    #     .prefetch_related("recipeingredient_set__ingredient", "reciperating_set")
    #     .all()
    # )
    # lookup_field = "slug"
    serializer_class = SimpleRecipeSerializer  # Default, overridden by get_serializer_class

    def get_queryset(self):
        """
        Optionally restricts the returned recipes to the logged-in user's recipes,
        by filtering against a `mine=true` query parameter in the URL.
        """
        user = self.request.user
        base_queryset = Recipe.objects.select_related("author").prefetch_related(
            "recipeingredient_set__ingredient", "reciperating_set"
        )

        # Filter for 'mine' parameter if user is authenticated
        show_mine = self.request.query_params.get("mine", "").lower() == "true"
        if show_mine and user.is_authenticated:
            queryset = base_queryset.filter(author=user)
        else:
            # Optionally, you might want to restrict viewing *all* recipes
            # if the user isn't authenticated, depending on your app's logic.
            # For now, returning all if 'mine' isn't specified or user isn't logged in.
            queryset = base_queryset.all()

        return queryset.order_by("-created_on")  # Apply ordering at the end

    def get_serializer_class(self):
        if self.action == "list":
            return SimpleRecipeSerializer
        return RecipeDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        # Save the recipe first to get an instance
        recipe_instance = serializer.save(author=self.request.user)
        # Create a corresponding FeedItem
        FeedItem.objects.create(
            user=recipe_instance.author,
            event_type=FeedItem.EventType.NEW_RECIPE,
            recipe=recipe_instance,
        )

    def perform_update(self, serializer):
        recipe_instance = serializer.save()
        # Similar to ratings: delete old feed item, create new
        FeedItem.objects.filter(recipe=recipe_instance, event_type=FeedItem.EventType.NEW_RECIPE).delete()
        FeedItem.objects.create(
            user=recipe_instance.author,
            event_type=FeedItem.EventType.NEW_RECIPE,
            recipe=recipe_instance,
        )

    def perform_destroy(self, instance):
        # Delete related feed items before deleting the recipe
        FeedItem.objects.filter(recipe=instance).delete()
        instance.delete()

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


class RecipeRatingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recipe ratings to be viewed or edited.
    Filters by recipe ID if 'recipe_id' query parameter is provided.
    """

    serializer_class = RecipeRatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    # filter_backends = [DjangoFilterBackend]
    filterset_fields = ["recipe"]

    def get_queryset(self):
        """
        Optionally restricts the returned ratings to a given recipe,
        by filtering against a `recipe_id` query parameter in the URL.
        """
        queryset = RecipeRating.objects.select_related("author").all()
        recipe_id = self.request.query_params.get("recipe")
        if recipe_id is not None:
            try:
                recipe_id_int = int(recipe_id)
                queryset = queryset.filter(recipe_id=recipe_id_int)
            except ValueError:
                return RecipeRating.objects.none()
        return queryset.order_by("-created_on")

    def perform_create(self, serializer):
        recipe = serializer.validated_data["recipe"]
        if RecipeRating.objects.filter(recipe=recipe, author=self.request.user).exists():
            raise serializers.ValidationError("You have already rated this recipe.")

        # Save the rating first to get an instance
        rating_instance = serializer.save(author=self.request.user)
        # Update recipe's average rating
        update_recipe_ratings(rating_instance.recipe)
        # Create a corresponding FeedItem
        FeedItem.objects.create(
            user=rating_instance.author,
            event_type=FeedItem.EventType.NEW_RATING,
            rating=rating_instance,
            recipe=rating_instance.recipe,
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        update_recipe_ratings(instance.recipe)
        # Delete the related feed item
        FeedItem.objects.filter(rating=instance).delete()
        FeedItem.objects.create(
            user=instance.author,
            event_type=FeedItem.EventType.NEW_RATING,
            rating=instance,
            recipe=instance.recipe,
        )

    def perform_destroy(self, instance):
        recipe = instance.recipe
        instance.delete()
        update_recipe_ratings(recipe)
        # Delete the related feed item
        FeedItem.objects.filter(rating=instance).delete()
