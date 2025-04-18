from django.contrib.auth.models import User
from django.db import models


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
    grocery_list = models.ForeignKey(GroceryList, related_name="plannedrecipes", on_delete=models.CASCADE)
    recipe = models.ForeignKey("recipes.Recipe", on_delete=models.CASCADE, related_name="plannedrecipes")
    guests = models.IntegerField()
    planned_on = models.DateField(blank=True, null=True)

    class Meta:
        get_latest_by = "timestamp"


class PlannedExtra(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    quantity = models.FloatField()  # quantity
    grocery_list = models.ForeignKey(GroceryList, related_name="plannedextras", on_delete=models.CASCADE)
    ingredient = models.ForeignKey("ingredients.Ingredient", on_delete=models.PROTECT, related_name="plannedextras")


class GroceryListItem(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    grocery_list = models.ForeignKey(GroceryList, related_name="grocerylistitems", on_delete=models.CASCADE)
    ingredient = models.ForeignKey("ingredients.Ingredient", on_delete=models.PROTECT, related_name="grocerylistitems")
    from_recipes = models.TextField()
    quantity = models.FloatField()
    is_checked = models.BooleanField(default=False)
