from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Recipe(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipe_posts")
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    ingredients = models.ManyToManyField("ingredients.Ingredient", through="RecipeIngredient", related_name="recipes")
    average_rating = models.FloatField(default=0.0)  # Stored as 0-10 scale
    rating_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    quantity = models.FloatField()  # quantity for 1 person
    ingredient = models.ForeignKey("ingredients.Ingredient", on_delete=models.PROTECT)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    unit = models.ForeignKey("ingredients.IngredientUnit", on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.ingredient.name} - {self.unit.name}"


class RecipeRating(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.author.username} - {self.recipe.title} - {self.rating}"
