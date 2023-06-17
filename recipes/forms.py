from django import forms
from .models import Recipe


class RecipeForm(forms.Form):
    recipe = forms.ModelChoiceField(
        queryset=Recipe.objects.all(), widget=forms.Select(attrs={"class": "form-control"})
    )
    guests = forms.IntegerField(
        min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"})
    )
