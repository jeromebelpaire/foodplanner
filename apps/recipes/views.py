from django.db.models import Case, IntegerField, Value, When
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.core.views import IsAuthorOrSuperuser
from apps.feed.models import FeedItem

from .models import Recipe, RecipeRating
from .permissions import IsAuthorOrReadOnly
from .serializers import RecipeDetailSerializer, RecipeRatingSerializer, SimpleRecipeSerializer
from .services import update_recipe_ratings


class PrioritizedSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_terms(request)

        if not search_terms:
            return queryset.order_by(*queryset.query.order_by)

        # Base queryset filtered by standard search (icontains)
        base_queryset = super().filter_queryset(request, queryset, view)

        # Annotate based on exact match (case-insensitive) for the *first* search term
        first_term = search_terms[0]
        annotated_queryset = base_queryset.annotate(
            is_exact_match=Case(
                When(title__iexact=first_term, then=Value(1)), default=Value(0), output_field=IntegerField()
            )
        )

        return annotated_queryset.order_by("-is_exact_match", *queryset.query.order_by)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class RecipeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recipes to be viewed, created, updated and deleted.
    Regular users can only modify their own recipes, superusers can modify any.
    Use ?mine=true to filter for the logged-in user's recipes.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrSuperuser]
    filter_backends = [PrioritizedSearchFilter]
    search_fields = ["title"]
    pagination_class = StandardResultsSetPagination
    serializer_class = SimpleRecipeSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned recipes to the logged-in user's recipes,
        by filtering against a `mine=true` query parameter in the URL.
        """
        user = self.request.user
        base_queryset = Recipe.objects.select_related("author").prefetch_related(
            "recipeingredient_set__ingredient", "reciperating_set"
        )

        show_mine = self.request.query_params.get("mine", "").lower() == "true"
        if show_mine and user.is_authenticated:
            queryset = base_queryset.filter(author=user)
        else:
            queryset = base_queryset.all()

        return queryset.order_by("-created_on")

    def get_serializer_class(self):
        if self.action == "list":
            return SimpleRecipeSerializer
        return RecipeDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        recipe_instance = serializer.save(author=self.request.user)
        FeedItem.objects.create(
            user=recipe_instance.author,
            event_type=FeedItem.EventType.NEW_RECIPE,
            recipe=recipe_instance,
        )

    def perform_update(self, serializer):
        recipe_instance = serializer.save()
        FeedItem.objects.filter(recipe=recipe_instance, event_type=FeedItem.EventType.NEW_RECIPE).delete()
        FeedItem.objects.create(
            user=recipe_instance.author,
            event_type=FeedItem.EventType.UPDATE_RECIPE,
            recipe=recipe_instance,
        )

    def perform_destroy(self, instance):
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
            scaled_ingredients.append(f"{ri.ingredient.name}: {quantity:.2f} {ri.unit.name}")

        return Response({"ingredients": scaled_ingredients})


class RecipeRatingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recipe ratings to be viewed or edited.
    Filters by recipe ID if 'recipe_id' query parameter is provided.
    """

    serializer_class = RecipeRatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
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

        rating_instance = serializer.save(author=self.request.user)
        update_recipe_ratings(rating_instance.recipe)
        FeedItem.objects.create(
            user=rating_instance.author,
            event_type=FeedItem.EventType.NEW_RATING,
            rating=rating_instance,
            recipe=rating_instance.recipe,
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        update_recipe_ratings(instance.recipe)
        FeedItem.objects.filter(rating=instance).delete()
        FeedItem.objects.create(
            user=instance.author,
            event_type=FeedItem.EventType.UPDATE_RATING,
            rating=instance,
            recipe=instance.recipe,
        )

    def perform_destroy(self, instance):
        recipe = instance.recipe
        instance.delete()
        update_recipe_ratings(recipe)
        FeedItem.objects.filter(rating=instance).delete()
