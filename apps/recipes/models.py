from django.contrib.auth.models import User
from django.db import models


class Recipe(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipe_posts")
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    ingredients = models.ManyToManyField("ingredients.Ingredient", through="RecipeIngredient", related_name="recipes")

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    quantity = models.FloatField()  # quantity for 1 person
    ingredient = models.ForeignKey("ingredients.Ingredient", on_delete=models.PROTECT)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.ingredient.name} - {self.ingredient.unit}"
