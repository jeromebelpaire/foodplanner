from django import forms
from .models import Recipe, GroceryList


class RecipeForm(forms.Form):
    recipes = forms.ModelMultipleChoiceField(
        queryset=Recipe.objects.all(), widget=forms.SelectMultiple(attrs={"class": "form-control"})
    )


class GroceryListForm(forms.Form):
    grocery_list = forms.ModelChoiceField(queryset=GroceryList.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(GroceryListForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["grocery_list"].queryset = GroceryList.objects.filter(user=user)
