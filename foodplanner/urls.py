"""foodplanner URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from django.views.generic.base import RedirectView

urlpatterns = (
    [
        path("", RedirectView.as_view(url=reverse_lazy("admin:index")), name="index"),
        path("admin/", admin.site.urls),
        path("accounts/", include("django.contrib.auth.urls")),
        path("api/", include("apps.core.urls")),
        path("api/feed/", include("apps.feed.urls")),
        path("api/recipes/", include("apps.recipes.urls")),
        path("api/ingredients/", include("apps.ingredients.urls")),
        path("api/groceries/", include("apps.groceries.urls")),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
