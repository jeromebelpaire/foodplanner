from django.urls import path
from . import views

urlpatterns = [
    path("csrf/", views.get_csrf, name="get_csrf"),  # TODO check
    path("login/", views.login_view, name="api_login"),  # TODO check
    path("auth/status/", views.auth_status, name="auth_status"),  # TODO switch to root
]
