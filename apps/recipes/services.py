from django.db.models import Avg, Count
from .models import Recipe, RecipeRating


def update_recipe_ratings(recipe: Recipe):
    """
    Calculates the average rating and count for a given recipe
    and updates its fields.
    """
    result = RecipeRating.objects.filter(recipe=recipe).aggregate(average=Avg("rating"), count=Count("id"))

    recipe.average_rating = result["average"] if result["average"] is not None else 0.0
    recipe.rating_count = result["count"]
    recipe.save(update_fields=["average_rating", "rating_count"])
