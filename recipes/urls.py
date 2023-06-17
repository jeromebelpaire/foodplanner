from django.urls import path
from . import views

urlpatterns = [
    path("recipe/<slug:recipe_slug>/<int:guests>/", views.recipe_view, name="recipe_view"),
    path("recipe/<slug:recipe_slug>/", views.recipe_view, name="recipe_view"),
]
