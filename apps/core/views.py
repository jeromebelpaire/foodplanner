from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()  # Get the active user model


class IsAuthorOrSuperuser(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or superusers to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author or superusers
        return obj.author == request.user or request.user.is_superuser


class CsrfTokenView(APIView):
    """Provides the CSRF token (if using SessionAuthentication)."""

    authentication_classes = []  # No auth needed to get CSRF token
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        token = get_token(request)
        return Response({"csrfToken": token})


class AuthStatusView(APIView):
    """Checks authentication status and returns basic user info if logged in."""

    # Uses default authentication classes defined in settings
    permission_classes = [permissions.AllowAny]  # Allow anyone to check

    def get(self, request, format=None):
        authenticated = request.user.is_authenticated
        response_data = {"authenticated": authenticated}
        if authenticated:
            # Return minimal, safe user details
            response_data["user"] = {
                "id": request.user.id,
                "username": request.user.username,
                "is_superuser": request.user.is_superuser,
            }
        return Response(response_data)


class LoginView(APIView):
    """
    API View for user login using Session Authentication.
    Expects 'username' and 'password' in JSON request body.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"detail": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response(
                {
                    "detail": "Successfully logged in.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "is_superuser": request.user.is_superuser,
                    },
                }
            )
        else:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


# You should also add a LogoutView
class LogoutView(APIView):
    """
    API View for user logout (Session Authentication).
    """

    def post(self, request, *args, **kwargs):
        logout(request)
        response = Response({"detail": "Successfully logged out."})

        # Explicitly delete the session cookie on logout for clarity/safety
        # Although django's logout() handles session invalidation
        # response.delete_cookie(settings.SESSION_COOKIE_NAME)
        # response.delete_cookie(settings.CSRF_COOKIE_NAME) # If needed

        return response
