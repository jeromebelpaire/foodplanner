function update_ingredients_list(data) {
  const ingredients = document.getElementById("ingredients");
  ingredients.innerHTML = "";

  Object.entries(data).forEach(([ingredient, details]) => {
    const li = document.createElement("li");
    li.classList.add("list-group-item");

    const input = document.createElement("input");
    input.type = "checkbox";
    input.classList.add("checkbox");
    li.appendChild(input);

    li.append(`${ingredient}: ${details.quantity} ${details.unit}`);

    const span = document.createElement("span");
    span.classList.add("small-text");
    span.textContent = ` for recipe(s): ${details.from_recipe}`;
    li.appendChild(span);

    ingredients.appendChild(li);
  });
}
