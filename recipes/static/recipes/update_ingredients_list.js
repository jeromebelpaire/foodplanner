function update_ingredients_list(data) {
  $("#ingredients").empty();
  for (var ingredient in data) {
    $("#ingredients").append(
      '<li class="list-group-item">' +
        ingredient +
        ": " +
        data[ingredient]["quantity"] +
        " " +
        data[ingredient]["unit"] +
        '<span class="small-text">' +
        " for recipe(s):  " +
        data[ingredient]["from_recipe"] +
        ' </span>'+
        "</li>"
    );
  }
}
