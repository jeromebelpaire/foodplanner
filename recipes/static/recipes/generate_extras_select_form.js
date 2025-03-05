function generate_extras_select_form(data) {
  // Update the recipe form HTML
  $("#extras-select-form").html(data.extras_form_html);
  $("#id_extras").change(function () {
    var selectedExtra = $(this).children("option:selected").length;
    $("#quantity").empty();
    for (i = 0; i < selectedExtra; i++) {
      $("#quantity").append(
        '<input type="number" name="quantity" min="1" class="form-control my-2" placeholder="Quantity of extra ' +
          (i + 1) +
          '">'
      );
    }
  });
}
