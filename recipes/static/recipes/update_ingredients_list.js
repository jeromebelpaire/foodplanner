function update_ingredients_list(data) {
  $("#ingredients").empty();
  for (var name in data) {
    $("#ingredients").append('<li class="list-group-item">' + name + ": " + data[name] + "</li>");
  }
}
