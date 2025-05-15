from django.db.models import Q, Case, When, Value, IntegerField
from rest_framework import viewsets, permissions, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Ingredient, IngredientUnit
from .serializers import IngredientSerializer, IngredientUnitSerializer

from rest_framework.pagination import PageNumberPagination


class PrioritizedSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_terms(request)

        if not search_terms:
            return queryset.order_by("-priority", *queryset.query.order_by)

        # Base queryset filtered by standard search (icontains)
        base_queryset = super().filter_queryset(request, queryset, view)

        # Annotate based on exact match (case-insensitive) for the *first* search term
        first_term = search_terms[0]
        annotated_queryset = base_queryset.annotate(
            is_exact_match=Case(
                When(name__iexact=first_term, then=Value(1)), default=Value(0), output_field=IntegerField()
            )
        )

        return annotated_queryset.order_by("-is_exact_match", "-priority", *queryset.query.order_by)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class IngredientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and potentially managing ingredients.
    Supports searching via the 'search' query parameter.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [PrioritizedSearchFilter]
    search_fields = ["name"]


class IngredientUnitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing available ingredient units.
    Read-only access for all users.
    """

    permission_classes = [permissions.AllowAny]
    queryset = IngredientUnit.objects.all()
    serializer_class = IngredientUnitSerializer
    pagination_class = None
