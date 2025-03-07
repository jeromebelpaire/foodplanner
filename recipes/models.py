from django.contrib.auth.models import User
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipe_posts")
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    quantity = models.FloatField()  # quantity for 1 person
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.ingredient.name} - {self.ingredient.unit}"


class GroceryList(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class PlannedRecipe(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    grocery_list = models.ForeignKey(GroceryList, related_name="items", on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="plannedrecipes")
    guests = models.IntegerField()

    class Meta:
        get_latest_by = "timestamp"

    def __str__(self):
        return f"{self.recipe.title} - {self.guests} guests"


class PlannedExtra(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    quantity = models.FloatField()  # quantity
    grocery_list = models.ForeignKey(GroceryList, related_name="plannedextras", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="plannedextras")

    def __str__(self):
        return f"{self.ingredient.name} - {str(self.quantity).removesuffix('.0')} {self.ingredient.unit}"
