function update_ingredients_list(data) {
  const ingredients = document.getElementById("ingredients");
  ingredients.innerHTML = "";

  for (let ingredient of data.ingredients) {
    const li = document.createElement("li");
    li.classList.add("list-group-item");

    const h5 = document.createElement("h5");
    h5.classList.add("mb-0");

    const span = document.createElement("span");
    span.classList.add("ingredient-name");
    span.innerText = ingredient;

    h5.appendChild(span);
    li.appendChild(h5);
    ingredients.appendChild(li);
  }
}
