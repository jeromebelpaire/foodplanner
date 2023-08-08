function update_ingredients_list(data) {
  $("#ingredients").empty();
  for (let ingredient of data.ingredients) {
    $("#ingredients").append(
      '<li class="list-group-item">' +
        '<h5 class="mb-0">' +
        '<span class="ingredient-name">' +
        ingredient +
        "</span>" +
        "</h5>" +
        "</li>"
    );
  }
}
