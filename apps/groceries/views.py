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

# Import the service function
from .services import update_grocery_list_items


class GroceryListViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users to manage their Grocery Lists (CRUD).
    """

    serializer_class = GroceryListSerializer
    permission_classes = [IsAuthenticated]
    # authentication_classes = [SessionAuthentication] # If needed

    def get_queryset(self):
        """Ensure users only see and manage their own grocery lists."""
        # Only return lists owned by the current authenticated user
        return GroceryList.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        """Associate the new grocery list with the current logged-in user."""
        serializer.save(user=self.request.user)

    # perform_update and perform_destroy automatically handle filtering by get_queryset


class PlannedRecipeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing recipes planned for a specific Grocery List.
    Filters by grocery_list ID provided in query parameters.
    """

    serializer_class = PlannedRecipeSerializer
    permission_classes = [IsAuthenticated]
    # authentication_classes = [SessionAuthentication] # If needed

    def get_queryset(self):
        """
        Filter planned recipes by the grocery_list query parameter
        and ensure the list belongs to the current user.
        """
        # Base queryset - all planned recipes belonging to the user
        queryset = PlannedRecipe.objects.filter(grocery_list__user=self.request.user)

        # For list view (multiple items), require grocery_list parameter
        if self.action == "list":
            grocery_list_id = self.request.query_params.get("grocery_list")
            if grocery_list_id:
                try:
                    # Further filter by the specific list ID
                    queryset = queryset.filter(grocery_list_id=int(grocery_list_id))
                except ValueError:
                    # Handle invalid grocery_list ID parameter
                    return PlannedRecipe.objects.none()  # Return empty queryset
            else:
                # If no grocery_list specified for list action, return none
                return PlannedRecipe.objects.none()

        return queryset.select_related("recipe").order_by("planned_on", "created_at")

    def perform_create(self, serializer):
        """
        Validate ownership of the target GroceryList before saving
        and trigger the grocery list item update.
        """
        # Ensure the grocery_list provided in the request data belongs to the user
        grocery_list = serializer.validated_data["grocery_list"]
        if grocery_list.user != self.request.user:
            raise PermissionDenied("You do not have permission to add items to this grocery list.")

        instance = serializer.save()
        # Trigger update logic after saving
        update_grocery_list_items(grocery_list_id=instance.grocery_list.id, user=self.request.user)

    def perform_update(self, serializer):
        """Ensure ownership on update and trigger recalculation."""
        # Check ownership of the original item via get_object (implicit via get_queryset)
        # Check ownership if grocery_list is being changed (if serializer allows it)
        if "grocery_list" in serializer.validated_data:
            new_grocery_list = serializer.validated_data["grocery_list"]
            if new_grocery_list.user != self.request.user:
                raise PermissionDenied("You cannot move this item to a list you do not own.")

        original_list_id = serializer.instance.grocery_list_id  # Get ID before saving
        new_instance = serializer.save()
        # Trigger update for the list it now belongs to
        update_grocery_list_items(grocery_list_id=new_instance.grocery_list.id, user=self.request.user)
        # If the list changed, trigger update for the old list as well
        if "grocery_list" in serializer.validated_data and original_list_id != new_instance.grocery_list_id:
            # Make sure the user owned the original list too before triggering update
            try:
                GroceryList.objects.get(id=original_list_id, user=self.request.user)
                update_grocery_list_items(grocery_list_id=original_list_id, user=self.request.user)
            except GroceryList.DoesNotExist:
                pass  # User didn't own original list, nothing to update for them

    def perform_destroy(self, instance):
        """
        Ensure ownership before deleting and trigger grocery list item update.
        Ownership is already checked by get_object via get_queryset.
        """
        grocery_list_id = instance.grocery_list.id  # Get the ID before deleting
        instance.delete()
        # Trigger update logic for the affected list after deleting
        # Need to re-check ownership in case get_queryset logic changes
        try:
            GroceryList.objects.get(id=grocery_list_id, user=self.request.user)
            update_grocery_list_items(grocery_list_id=grocery_list_id, user=self.request.user)
        except GroceryList.DoesNotExist:
            # Should not happen if get_queryset is correct, but good practice
            print(
                f"Warning: Could not trigger update for list {grocery_list_id} after delete, list not found or owned."
            )
            pass


# --- Identical structure for PlannedExtraViewSet ---


class PlannedExtraViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing extra ingredients planned for a specific Grocery List.
    Filters by grocery_list ID provided in query parameters.
    """

    serializer_class = PlannedExtraSerializer
    permission_classes = [IsAuthenticated]
    # authentication_classes = [SessionAuthentication] # If needed

    def get_queryset(self):
        """Filter planned extras by grocery_list and user ownership."""
        # Base queryset - all planned extras belonging to the user
        queryset = PlannedExtra.objects.filter(grocery_list__user=self.request.user)

        # For list view (multiple items), require grocery_list parameter
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
    # authentication_classes = [SessionAuthentication] # If needed
    # Allow GET for listing, PATCH for updating 'is_checked', HEAD/OPTIONS. Disallow POST/PUT/DELETE.
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        """Filter grocery list items by grocery_list and user ownership."""
        # Base queryset - all grocery list items belonging to the user
        queryset = GroceryListItem.objects.filter(grocery_list__user=self.request.user)

        # For list view (multiple items), require grocery_list parameter
        if self.action == "list":
            grocery_list_id = self.request.query_params.get("grocery_list")
            if grocery_list_id:
                try:
                    queryset = queryset.filter(grocery_list_id=int(grocery_list_id))
                except ValueError:
                    return GroceryListItem.objects.none()
            else:
                # Might be useful to see *all* items across lists, but usually UI is list-specific
                return GroceryListItem.objects.none()

        # Ordering defined in model Meta, but can override here if needed
        return queryset.select_related("ingredient")  # Efficiently fetch ingredient details

    def perform_update(self, serializer):
        """
        Allows updating fields defined in the serializer (primarily 'is_checked').
        Ownership is checked by get_queryset/get_object.
        """
        # Additional check just to be absolutely sure (belt and braces)
        instance = self.get_object()  # Fetches the instance based on URL pk
        if instance.grocery_list.user != self.request.user:
            raise PermissionDenied("You cannot update items from a grocery list you do not own.")

        # Only save fields provided in the PATCH request
        serializer.save()

    # DELETE and CREATE are disabled via http_method_names
