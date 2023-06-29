function update_ingredients_list(data) {
  console.log(data);
  $("#ingredients").empty();
  for (var name in data) {
    $("#ingredients").append('<li class="list-group-item">' + name + ": " + data[name] + "</li>");
  }
}
