from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of an object to edit it,
    unless the user is a superuser.
    Assumes the model instance has an `author` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request (GET, HEAD, OPTIONS).
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are allowed if the user is a superuser OR
        # if the user is the author of the rating.
        return request.user.is_superuser or obj.author == request.user
