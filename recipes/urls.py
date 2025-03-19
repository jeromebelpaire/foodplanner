from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home_view, name="home_view"),
    path("get_recipes/", views.get_recipes, name="get_recipes"),
    path("recipe/<slug:recipe_slug>/", views.recipe_view, name="recipe_uncounted_view"),
    path("recipe/<slug:recipe_slug>/<int:guests>/", views.recipe_view, name="recipe_view"),
    path("recipe_sum/", views.recipe_sum_view, name="recipe_sum_view"),
    path("save_planned_recipe/", views.save_planned_recipe, name="save_planned_recipe"),
    path("save_planned_extra/", views.save_planned_extra, name="save_planned_extra"),
    path(
        "get_formatted_ingredients/<slug:recipe_slug>/<int:guests>/",
        views.get_formatted_ingredients,
        name="get_formatted_ingredients",
    ),
    path("get_recipe_info/<slug:recipe_slug>/", views.get_recipe_info, name="get_recipe_info"),
    path("get_planned_ingredients/", views.get_planned_ingredients, name="get_planned_ingredients"),
    path("create_grocery_list/", views.create_grocery_list, name="create_grocery_list"),
    path("delete_grocery_list/", views.delete_grocery_list, name="delete_grocery_list"),
    path("get_planned_recipes/", views.get_planned_recipes, name="get_planned_recipes"),
    path("get_planned_extras/", views.get_planned_extras, name="get_planned_extras"),
    path(
        "plannedrecipes/<int:planned_recipe_id>/delete/",
        views.delete_planned_recipe,
        name="delete_planned_recipe",
    ),
    path("plannedextras/<int:planned_extra_id>/delete/", views.delete_planned_extra, name="delete_planned_extra"),
    path(
        "generate_recipe_select_form/",
        views.generate_recipe_select_form,
        name="generate_recipe_select_form",
    ),
]
