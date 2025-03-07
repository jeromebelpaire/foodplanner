function generate_extras_select_form(data) {
  document.getElementById("extras-select-form").innerHTML = data.extras_form_html;
  
  const extras = document.getElementById("id_extras");
  extras.addEventListener("change", function () {

    const selectedExtra = this.selectedOptions.length;
    const quantity = document.getElementById('quantity')

    quantity.innerHTML = "";

    for (i = 0; i < selectedExtra; i++) {
      const input = document.createElement("input");
      input.type = "number";
      input.name = "quantity";
      input.min = "1";
      input.className = "form-control my-2";
      input.placeholder = "Quantity of extra " + (i + 1);
      quantity.appendChild(input);
      }
  })
}