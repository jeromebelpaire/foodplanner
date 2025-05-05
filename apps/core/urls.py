from django.urls import path

from .views import (
    AuthStatusView,
    CsrfTokenView,
    FollowersListView,
    FollowingListView,
    FollowToggleView,
    LoginView,
    LogoutView,
    SignupView,
    UserSearchView,
)

app_name = "core"

urlpatterns = [
    path("auth/csrf/", CsrfTokenView.as_view(), name="auth-csrf"),
    path("auth/status/", AuthStatusView.as_view(), name="auth-status"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/signup/", SignupView.as_view(), name="auth-signup"),
    path("users/search/", UserSearchView.as_view(), name="user-search"),
    path("users/<int:pk>/follow/", FollowToggleView.as_view(), name="user-follow-toggle"),
    path("users/followers/", FollowersListView.as_view(), name="user-followers"),
    path("users/following/", FollowingListView.as_view(), name="user-following"),
]
