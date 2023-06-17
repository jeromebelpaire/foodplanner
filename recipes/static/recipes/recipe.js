// The original quantities for one guest
const originalQuantities = Array.from(document.querySelectorAll(".ingredient-quantity")).map(
  (span) => parseFloat(span.textContent)
);

document.getElementById("increase-guests").addEventListener("click", function () {
  updateGuestCount(1);
});

document.getElementById("decrease-guests").addEventListener("click", function () {
  updateGuestCount(-1);
});

function updateGuestCount(change) {
  const guestCountSpan = document.getElementById("guest-count");
  let guestCount = parseInt(guestCountSpan.textContent);

  // Don't decrease the guest count below 1
  if (guestCount === 1 && change === -1) {
    return;
  }

  guestCount += change;
  guestCountSpan.textContent = guestCount;

  // Update the quantities
  const quantitySpans = document.querySelectorAll(".ingredient-quantity");
  for (let i = 0; i < quantitySpans.length; i++) {
    quantitySpans[i].textContent = (originalQuantities[i] * guestCount).toFixed(2);
  }
}
