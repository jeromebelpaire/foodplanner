from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.authentication import SessionAuthentication  # Or TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import GroceryList, PlannedRecipe, PlannedExtra, GroceryListItem
from .serializers import (
    GroceryListSerializer,
    PlannedRecipeSerializer,
    PlannedExtraSerializer,
    GroceryListItemSerializer,
)

from .services import update_grocery_list_items


class GroceryListViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users to manage their Grocery Lists (CRUD).
    """

    serializer_class = GroceryListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Ensure users only see and manage their own grocery lists."""
        return GroceryList.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        """Associate the new grocery list with the current logged-in user."""
        serializer.save(user=self.request.user)


class PlannedRecipeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing recipes planned for a specific Grocery List.
    Filters by grocery_list ID provided in query parameters.
    """

    serializer_class = PlannedRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter planned recipes by the grocery_list query parameter
        and ensure the list belongs to the current user.
        """
        queryset = PlannedRecipe.objects.filter(grocery_list__user=self.request.user)

        if self.action == "list":
            grocery_list_id = self.request.query_params.get("grocery_list")
            if grocery_list_id:
                try:
                    queryset = queryset.filter(grocery_list_id=int(grocery_list_id))
                except ValueError:
                    return PlannedRecipe.objects.none()
            else:
                return PlannedRecipe.objects.none()

        return queryset.select_related("recipe").order_by("planned_on", "created_at")

    def perform_create(self, serializer):
        """
        Validate ownership of the target GroceryList before saving
        and trigger the grocery list item update.
        """
        grocery_list = serializer.validated_data["grocery_list"]
        if grocery_list.user != self.request.user:
            raise PermissionDenied("You do not have permission to add items to this grocery list.")

        instance = serializer.save()
        update_grocery_list_items(grocery_list_id=instance.grocery_list.id, user=self.request.user)

    def perform_update(self, serializer):
        """Ensure ownership on update and trigger recalculation."""
        if "grocery_list" in serializer.validated_data:
            new_grocery_list = serializer.validated_data["grocery_list"]
            if new_grocery_list.user != self.request.user:
                raise PermissionDenied("You cannot move this item to a list you do not own.")

        original_list_id = serializer.instance.grocery_list_id  # Get ID before saving
        new_instance = serializer.save()
        update_grocery_list_items(grocery_list_id=new_instance.grocery_list.id, user=self.request.user)
        if "grocery_list" in serializer.validated_data and original_list_id != new_instance.grocery_list_id:
            try:
                GroceryList.objects.get(id=original_list_id, user=self.request.user)
                update_grocery_list_items(grocery_list_id=original_list_id, user=self.request.user)
            except GroceryList.DoesNotExist:
                pass

    def perform_destroy(self, instance):
        """
        Ensure ownership before deleting and trigger grocery list item update.
        Ownership is already checked by get_object via get_queryset.
        """
        grocery_list_id = instance.grocery_list.id
        instance.delete()
        # Trigger update logic for the affected list after deleting
        # Need to re-check ownership in case get_queryset logic changes
        try:
            GroceryList.objects.get(id=grocery_list_id, user=self.request.user)
            update_grocery_list_items(grocery_list_id=grocery_list_id, user=self.request.user)
        except GroceryList.DoesNotExist:
            print(
                f"Warning: Could not trigger update for list {grocery_list_id} after delete, list not found or owned."
            )
            pass


class PlannedExtraViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing extra ingredients planned for a specific Grocery List.
    Filters by grocery_list ID provided in query parameters.
    """

    serializer_class = PlannedExtraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter planned extras by grocery_list and user ownership."""
        queryset = PlannedExtra.objects.filter(grocery_list__user=self.request.user)

        if self.action == "list":
            grocery_list_id = self.request.query_params.get("grocery_list")
            if grocery_list_id:
                try:
                    queryset = queryset.filter(grocery_list_id=int(grocery_list_id))
                except ValueError:
                    return PlannedExtra.objects.none()
            else:
                return PlannedExtra.objects.none()

        return queryset.select_related("ingredient").order_by("ingredient__name")

    def perform_create(self, serializer):
        """Validate ownership and trigger update."""
        grocery_list = serializer.validated_data["grocery_list"]
        if grocery_list.user != self.request.user:
            raise PermissionDenied("You do not have permission to add items to this grocery list.")
        instance = serializer.save()
        update_grocery_list_items(grocery_list_id=instance.grocery_list.id, user=self.request.user)

    def perform_update(self, serializer):
        """Ensure ownership on update and trigger recalculation."""
        if "grocery_list" in serializer.validated_data:
            new_grocery_list = serializer.validated_data["grocery_list"]
            if new_grocery_list.user != self.request.user:
                raise PermissionDenied("You cannot move this item to a list you do not own.")

        original_list_id = serializer.instance.grocery_list_id
        new_instance = serializer.save()
        update_grocery_list_items(grocery_list_id=new_instance.grocery_list.id, user=self.request.user)
        if "grocery_list" in serializer.validated_data and original_list_id != new_instance.grocery_list_id:
            try:
                GroceryList.objects.get(id=original_list_id, user=self.request.user)
                update_grocery_list_items(grocery_list_id=original_list_id, user=self.request.user)
            except GroceryList.DoesNotExist:
                pass

    def perform_destroy(self, instance):
        """Ensure ownership and trigger update."""
        grocery_list_id = instance.grocery_list.id
        instance.delete()
        try:
            GroceryList.objects.get(id=grocery_list_id, user=self.request.user)
            update_grocery_list_items(grocery_list_id=grocery_list_id, user=self.request.user)
        except GroceryList.DoesNotExist:
            print(
                f"Warning: Could not trigger update for list {grocery_list_id} after delete, list not found or owned."
            )
            pass


class GroceryListItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and updating items within a generated Grocery List.
    Primarily used for listing items and marking them as checked/unchecked (PATCH).
    Filters by grocery_list ID provided in query parameters.
    """

    serializer_class = GroceryListItemSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        """Filter grocery list items by grocery_list and user ownership."""
        queryset = GroceryListItem.objects.filter(grocery_list__user=self.request.user)

        if self.action == "list":
            grocery_list_id = self.request.query_params.get("grocery_list")
            if grocery_list_id:
                try:
                    queryset = queryset.filter(grocery_list_id=int(grocery_list_id))
                except ValueError:
                    return GroceryListItem.objects.none()
            else:
                return GroceryListItem.objects.none()

        return queryset.select_related("ingredient")

    def perform_update(self, serializer):
        """
        Allows updating fields defined in the serializer (primarily 'is_checked').
        Ownership is checked by get_queryset/get_object.
        """
        instance = self.get_object()
        if instance.grocery_list.user != self.request.user:
            raise PermissionDenied("You cannot update items from a grocery list you do not own.")

        serializer.save()
