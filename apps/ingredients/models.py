from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    fdc_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class IngredientUnit(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
