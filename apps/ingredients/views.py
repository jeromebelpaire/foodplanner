from django.db.models import Q, Case, When, Value, IntegerField
from rest_framework import viewsets, permissions, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Ingredient
from .serializers import IngredientSerializer

from rest_framework.pagination import PageNumberPagination


class PrioritizedSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_terms(request)

        if not search_terms:
            # If no search term, still respect priority and default ordering
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

        # Order by exact match first, then priority, then the default ordering
        # Note: queryset.query.order_by contains the default ordering ('name')
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
    # Use the custom filter backend
    filter_backends = [PrioritizedSearchFilter]
    search_fields = ["name"]

    # If read-only is strictly required:
    # http_method_names = ['get', 'head', 'options']
