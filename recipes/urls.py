from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home_view, name="home_view"),
    path("recipe/<slug:recipe_slug>/", views.recipe_view, name="recipe_uncounted_view"),
    path("recipe/<slug:recipe_slug>/<int:guests>/", views.recipe_view, name="recipe_view"),
    path("recipe_sum/", views.recipe_sum_view, name="recipe_sum_view"),
    path("save_planned_recipe/", views.save_planned_recipe, name="save_planned_recipe"),
    path("get_planned_ingredients/", views.get_planned_ingredients, name="get_planned_ingredients"),
]
