from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly

# from rest_framework.authentication import SessionAuthentication

from .models import Ingredient
from .serializers import IngredientSerializer

# from rest_framework.pagination import PageNumberPagination

# class StandardResultsSetPagination(PageNumberPagination):
#     page_size = 25
#     page_size_query_param = 'page_size'
#     max_page_size = 100


class IngredientViewSet(viewsets.ModelViewSet):  # Changed to ModelViewSet if you want CRUD later
    """
    API endpoint for viewing and potentially managing ingredients.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]  # Allow viewing, restrict edits
    # authentication_classes = [SessionAuthentication] # If needed
    queryset = Ingredient.objects.all()  # Ordering is defined in Model Meta
    serializer_class = IngredientSerializer
    # pagination_class = StandardResultsSetPagination # Enable if needed
    # Add search/filtering if the list grows large
    # filter_backends = [filters.SearchFilter]
    # search_fields = ['name']

    # If read-only is strictly required:
    # http_method_names = ['get', 'head', 'options']
