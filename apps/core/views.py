from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from rest_framework import permissions, status, serializers
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


# Serializer for User creation
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, required=True, label="Confirm password")

    class Meta:
        model = User
        fields = ("id", "username", "password", "email", "first_name", "last_name", "confirm_password")
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class SignupView(APIView):
    """
    API View for user signup. Creates a new user.
    Expects 'username', 'password', 'email', 'first_name', 'last_name'.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "detail": "User created successfully.",
                    "user": UserSerializer(user, context={"request": request}).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
