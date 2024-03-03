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

    // Attach the click event listener to the delete button
    deleteButton.addEventListener("click", function () {
      deleteRecipe(this.getAttribute("data-id"));
    });

    li.appendChild(deleteButton);
    plannedRecipesList.appendChild(li);
  });
}

function deleteRecipe(recipeId) {
  // Define your delete logic here, similar to the previous example
  const deleteUrl = `/recipes/plannedrecipes/${recipeId}/delete/`; // Adjust accordingly FIXME
  fetch(deleteUrl, {
    method: "DELETE",
  })
    .then((response) => {
      if (response.ok) {
        // Successfully deleted, now remove the list item from the DOM
        document.getElementById(`planned-recipe-${recipeId}`).remove();
      } else {
        alert("There was an error deleting the planned recipe.");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("There was an error deleting the planned recipe.");
    });
}
