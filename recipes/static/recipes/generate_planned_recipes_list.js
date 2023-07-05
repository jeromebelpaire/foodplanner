function generate_planned_recipes_list(data) {
  $("#planned-recipes").empty();
  for (var planned_recipe in data) {
    $("#planned-recipes").append(
      '<li class="list-group-item" id="planned-recipe-' +
      data[planned_recipe]["id"] +
      '">' +
        data[planned_recipe]["str"] +
        '<button class="btn btn-danger float-right delete-button" data-id="'+
        data[planned_recipe]["id"] +
        '">Delete</button>' +
        "</li>"
    );
  }
}
