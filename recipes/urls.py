from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home_view, name="home_view"),
    path("recipe/<slug:recipe_slug>/", views.recipe_view, name="recipe_uncounted_view"),
    path("recipe/<slug:recipe_slug>/<int:guests>/", views.recipe_view, name="recipe_view"),
    path("recipe_sum/", views.recipe_sum_view, name="recipe_sum_view"),
    path("save_grocery_list/", views.save_grocery_list, name="save_grocery_list"),
    path("get_grocery_list/", views.get_grocery_list, name="get_grocery_list"),
]
