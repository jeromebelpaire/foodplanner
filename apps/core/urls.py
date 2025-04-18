from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("auth/csrf/", views.CsrfTokenView.as_view(), name="auth-csrf"),
    path("auth/status/", views.AuthStatusView.as_view(), name="auth-status"),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
]
