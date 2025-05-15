from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Allows read-only access for any request.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        # Assumes the object model has a 'user' attribute.
        if not hasattr(obj, "user"):
            # If the object doesn't have a user attribute, deny permission
            # Or handle based on specific logic (e.g., check an 'author' attribute)
            return False

        # Check if the user is the owner OR a superuser
        return obj.user == request.user or request.user.is_superuser
