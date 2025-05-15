from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from rest_framework import permissions, status, serializers, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, APIException
from rest_framework.pagination import PageNumberPagination
from django.db.models import Case, When, Value, IntegerField
from django.utils import timezone

from .models import Follow, UserProfile, TermsOfServiceVersion
from .serializers import UserSearchSerializer, TermsOfServiceVersionSerializer

User = get_user_model()


class IsAuthorOrSuperuser(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or superusers to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user or request.user.is_superuser


class CsrfTokenView(APIView):
    """Provides the CSRF token (if using SessionAuthentication)."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        token = get_token(request)
        return Response({"csrfToken": token})


class AuthStatusView(APIView):
    """Checks authentication status and returns basic user info if logged in."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        authenticated = request.user.is_authenticated
        response_data = {"authenticated": authenticated}
        if authenticated:
            response_data["user"] = {
                "id": request.user.id,
                "username": request.user.username,
                "is_superuser": request.user.is_superuser,
                "follower_count": request.user.followers_set.count(),
                "following_count": request.user.following_set.count(),
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


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, required=True, label="Confirm password")
    accept_tos = serializers.BooleanField(write_only=True, required=True, label="Accept Terms of Service")

    class Meta:
        model = User
        fields = ("id", "username", "password", "email", "first_name", "last_name", "confirm_password", "accept_tos")
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "first_name": {"required": False, "allow_blank": True, "write_only": True},
            "last_name": {"required": False, "allow_blank": True, "write_only": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def validate_accept_tos(self, value):
        """Ensure the ToS checkbox was checked. Temporarily allows None/False."""
        if not value:
            raise serializers.ValidationError("You must accept the Terms of Service to register.")
        return value

    def create(self, validated_data):
        accepted_tos_data = validated_data.pop("accept_tos")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        profile_tos_accepted_at = None
        profile_accepted_tos_version = None

        try:
            latest_tos = TermsOfServiceVersion.objects.filter(published_at__lte=timezone.now()).latest("published_at")
            profile_accepted_tos_version = latest_tos
            profile_tos_accepted_at = timezone.now()
        except TermsOfServiceVersion.DoesNotExist:
            raise APIException(
                detail="We are unable to process your signup at this time due to a configuration issue. Please try again later or contact support if the problem persists.",
                code="tos_version_missing",
            )

        UserProfile.objects.create(
            user=user, tos_accepted_at=profile_tos_accepted_at, accepted_tos_version=profile_accepted_tos_version
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


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination configuration.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class UserSearchView(generics.ListAPIView):
    """
    API view to search for users by username.
    Requires authentication.
    Uses pagination (default DRF settings apply).
    Returns user data including whether the requesting user follows them.
    """

    serializer_class = UserSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Filter users based on the 'query' parameter (username) for search,
        or provide suggestions if no query is given.
        Suggestions prioritize users following the current user, then 'friends of friends'.
        Excludes the current user and users they already follow.
        """
        request_user = self.request.user
        search_query = self.request.query_params.get("query", None)

        followed_pks = set(request_user.following_set.values_list("followed_id", flat=True))

        if search_query:
            queryset = (
                User.objects.filter(username__icontains=search_query).exclude(pk=request_user.pk)  # Exclude self
                # Optional: exclude already followed users from search results too?
                # .exclude(pk__in=followed_pks)
                .order_by("username")
            )
        else:
            if not request_user.is_authenticated:
                return User.objects.none()

            # Tier 1: Users following the request user but not followed back
            follower_pks = set(request_user.followers_set.values_list("follower_id", flat=True))
            tier1_pks = follower_pks - followed_pks

            # Tier 2: Users followed by people the request user follows ("friends of friends")
            people_user_follows_pks = followed_pks
            tier2_candidates_pks = set(
                Follow.objects.filter(follower_id__in=people_user_follows_pks)
                .exclude(followed_id=request_user.pk)
                .exclude(followed_id__in=followed_pks)
                .exclude(followed_id__in=tier1_pks)
                .values_list("followed_id", flat=True)
            )

            # Tier 3: Other users (not self, not followed, not in tier 1 or 2)
            excluded_pks_for_tier3 = followed_pks | tier1_pks | tier2_candidates_pks | {request_user.pk}
            tier3_pks = set(User.objects.exclude(pk__in=excluded_pks_for_tier3).values_list("pk", flat=True))

            all_suggestion_pks = tier1_pks.union(tier2_candidates_pks).union(tier3_pks)

            if not all_suggestion_pks:
                return User.objects.none()

            queryset = (
                User.objects.filter(pk__in=all_suggestion_pks)
                .annotate(
                    suggestion_priority=Case(
                        When(pk__in=tier1_pks, then=Value(1)),  # Higher priority for followers
                        When(pk__in=tier2_candidates_pks, then=Value(2)),  # Medium priority for FoF
                        default=Value(3),  # Lowest priority for others
                        output_field=IntegerField(),
                    )
                )
                .order_by("suggestion_priority", "username")
            )

        return queryset

    def get_serializer_context(self):
        """Pass request context to the serializer for 'is_following'."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class FollowToggleView(APIView):
    """
    API view to follow or unfollow a user.
    Expects a POST request to follow and a DELETE request to unfollow.
    The user to follow/unfollow is specified in the URL (pk).
    Requires authentication.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, format=None):
        """Follow a user specified by pk."""
        try:
            user_to_follow = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound("User not found.")

        follower = request.user

        if follower == user_to_follow:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        if Follow.objects.filter(follower=follower, followed=user_to_follow).exists():
            return Response({"detail": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(follower=follower, followed=user_to_follow)
        return Response({"detail": f"Successfully followed {user_to_follow.username}."}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, format=None):
        """Unfollow a user specified by pk."""
        try:
            user_to_unfollow = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound("User not found.")

        follower = request.user

        try:
            follow_instance = Follow.objects.get(follower=follower, followed=user_to_unfollow)
            follow_instance.delete()
            return Response(
                {"detail": f"Successfully unfollowed {user_to_unfollow.username}."}, status=status.HTTP_204_NO_CONTENT
            )
        except Follow.DoesNotExist:
            return Response({"detail": "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)


class FollowersListView(generics.ListAPIView):
    """
    API view to list users who are following the authenticated user.
    Requires authentication.
    Uses pagination.
    Returns user data including whether the authenticated user follows them back.
    """

    serializer_class = UserSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Return users who follow the request.user."""
        request_user = self.request.user
        follower_ids = Follow.objects.filter(followed=request_user).values_list("follower_id", flat=True)
        queryset = User.objects.filter(pk__in=follower_ids).order_by("username")
        return queryset

    def get_serializer_context(self):
        """Pass request context to the serializer for 'is_following'."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class FollowingListView(generics.ListAPIView):
    """
    API view to list users whom the authenticated user is following.
    Requires authentication.
    Uses pagination.
    Returns user data including whether the authenticated user follows them (always true here).
    """

    serializer_class = UserSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Return users followed by the request.user."""
        request_user = self.request.user
        followed_ids = Follow.objects.filter(follower=request_user).values_list("followed_id", flat=True)
        queryset = User.objects.filter(pk__in=followed_ids).order_by("username")
        return queryset

    def get_serializer_context(self):
        """Pass request context to the serializer for 'is_following'."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class LatestTermsOfServiceView(APIView):
    """
    Provides the content of the latest published Terms of Service.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        try:
            latest_tos = TermsOfServiceVersion.objects.filter(published_at__lte=timezone.now()).latest("published_at")
            serializer = TermsOfServiceVersionSerializer(latest_tos)
            return Response(serializer.data)
        except TermsOfServiceVersion.DoesNotExist:
            return Response({"detail": "No published Terms of Service found."}, status=status.HTTP_404_NOT_FOUND)
