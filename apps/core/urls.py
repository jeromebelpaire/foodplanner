from django.urls import path
from .views import CsrfTokenView, LoginView, LogoutView, AuthStatusView, SignupView

app_name = "core"

urlpatterns = [
    path("auth/csrf/", CsrfTokenView.as_view(), name="auth-csrf"),
    path("auth/status/", AuthStatusView.as_view(), name="auth-status"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/signup/", SignupView.as_view(), name="auth-signup"),
]
