function generate_recipe_select_form(data) {
  document.getElementById("recipe-select-form").innerHTML = data.recipe_form_html;

  const idRecipesEl = document.getElementById("id_recipes");
  idRecipesEl.addEventListener("change", function () {
    // Get the count of selected options (works for a multi-select)
    const selectedRecipes = this.selectedOptions.length;
    const guestsEl = document.getElementById("guests");

    guestsEl.innerHTML = "";

    for (let i = 0; i < selectedRecipes; i++) {
      const input = document.createElement("input");
      input.type = "number";
      input.name = "guests";
      input.min = "1";
      input.className = "form-control my-2";
      input.placeholder = "Number of guests for recipe " + (i + 1);
      guestsEl.appendChild(input);
    }
  });
}
