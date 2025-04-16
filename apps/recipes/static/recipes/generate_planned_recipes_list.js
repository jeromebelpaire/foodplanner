function generate_planned_recipes_list(data) {
  const plannedRecipesList = document.getElementById("planned-recipes");
  plannedRecipesList.innerHTML = ""; // Clear the list

  Object.keys(data).forEach((key) => {
    const plannedRecipe = data[key];
    const li = document.createElement("li");
    li.className = "list-group-item";
    li.id = `planned-recipe-${plannedRecipe["id"]}`;

    const textNode = document.createTextNode(plannedRecipe["str"]);
    li.appendChild(textNode);

    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.className = "btn btn-danger float-right delete-button";
    deleteButton.setAttribute("data-id", plannedRecipe["id"]);

    deleteButton.setAttribute("data-delete-url", plannedRecipe["delete_url"]);

    // Attach the click event listener to the delete button
    deleteButton.addEventListener("click", function () {
      deleteRecipe(this.getAttribute("data-delete-url"));
    });

    li.appendChild(deleteButton);
    plannedRecipesList.appendChild(li);
  });
}

function deleteRecipe(deleteUrl) {
  const csrftoken = getCookie("csrftoken");
  console.log("deleting with token: ", csrftoken);
  fetch(deleteUrl, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => {
      if (response.ok) {
        // Find the button's parent <li> and remove it from the DOM
        document.querySelector(`[data-delete-url="${deleteUrl}"]`).closest("li").remove();
      } else {
        alert("There was an error deleting the planned recipe.");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("There was an error deleting the planned recipe.");
    });
}
