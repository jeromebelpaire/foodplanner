function generate_recipe_select_form(data) {
  // Update the recipe form HTML
  $("#recipe-form").html(data.recipe_form_html);
  $("#id_recipes").change(function () {
    var selectedRecipes = $(this).children("option:selected").length;
    $("#guests").empty();
    for (i = 0; i < selectedRecipes; i++) {
      $("#guests").append(
        '<input type="number" name="guests" min="1" class="form-control my-2" placeholder="Number of guests for recipe ' +
          (i + 1) +
          '">'
      );
    }
  });
}
