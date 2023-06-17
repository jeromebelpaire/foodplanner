from django import forms
from .models import Recipe


class RecipeForm(forms.Form):
    recipes = forms.ModelMultipleChoiceField(
        queryset=Recipe.objects.all(), widget=forms.SelectMultiple(attrs={"class": "form-control"})
    )
