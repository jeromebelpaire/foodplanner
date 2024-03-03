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

    // Replace 'PLACEHOLDER' in the template URL with the actual recipe ID
    const deleteUrl = deleteUrlTemplate.replace("99999999", plannedRecipe["id"]);
    deleteButton.setAttribute("data-delete-url", deleteUrl);

    // Attach the click event listener to the delete button
    deleteButton.addEventListener("click", function () {
      deleteRecipe(this.getAttribute("data-delete-url"));
    });

    li.appendChild(deleteButton);
    plannedRecipesList.appendChild(li);
  });
}

function deleteRecipe(deleteUrl) {
  // Use the provided deleteUrl directly, which now includes the correct recipe ID
  fetch(deleteUrl, {
    method: "DELETE",
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
