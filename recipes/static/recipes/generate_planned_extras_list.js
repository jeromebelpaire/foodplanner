function generate_planned_extras_list(data) {
  const plannedExtrasList = document.getElementById("planned-extras");
  plannedExtrasList.innerHTML = ""; // Clear the list

  Object.keys(data).forEach((key) => {
    const plannedExtra = data[key];
    const li = document.createElement("li");
    li.className = "list-group-item";
    li.id = `planned-extra-${plannedExtra["id"]}`;

    const textNode = document.createTextNode(plannedExtra["str"]);
    li.appendChild(textNode);

    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.className = "btn btn-danger float-right delete-button";
    deleteButton.setAttribute("data-id", plannedExtra["id"]);

    // Replace 'PLACEHOLDER' in the template URL with the actual extra ID
    deleteButton.setAttribute("data-delete-url", plannedExtra["delete_url"]);

    // Attach the click event listener to the delete button
    deleteButton.addEventListener("click", function () {
      deleteExtra(this.getAttribute("data-delete-url"));
    });

    li.appendChild(deleteButton);
    plannedExtrasList.appendChild(li);
  });
}

function deleteExtra(deleteUrl) {
  fetch(deleteUrl, {
    method: "DELETE",
  })
    .then((response) => {
      if (response.ok) {
        // Find the button's parent <li> and remove it from the DOM
        document.querySelector(`[data-delete-url="${deleteUrl}"]`).closest("li").remove();
      } else {
        alert("There was an error deleting the planned extra.");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("There was an error deleting the planned extra.");
    });
}
