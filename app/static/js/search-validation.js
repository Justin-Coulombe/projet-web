"use strict";
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("research");
  if (!form) return;
  const start = form.querySelector('[name="debut"]');
  const end = form.querySelector('[name="fin"]');
  const filter = form.querySelector('[name="filter"]');

  function show(field, text) {
    if (!field) return;
    field.classList.toggle("is-invalid", !!text);
    field.setAttribute("aria-invalid", String(!!text));
    let node = field.parentElement.querySelector(".search-feedback");
    if (!node) {
      node = document.createElement("div");
      node.className = "invalid-feedback d-block search-feedback";
      field.insertAdjacentElement("afterend", node);
    }
    node.textContent = text;
  }
  function valid() {
    let error = "";
    if (start?.value && Number.isNaN(new Date(start.value).getTime())) error = "Date de début invalide.";
    if (end?.value && Number.isNaN(new Date(end.value).getTime())) error = "Date de fin invalide.";
    if (start?.value && end?.value && new Date(start.value) > new Date(end.value))
      error = "La fin doit suivre le début.";
    show(end, error);
    const badFilter = filter && !["Tous", "Intérieur", "Extérieur"].includes(filter.value);
    show(filter, badFilter ? "Choisissez un filtre valide." : "");
    return !error && !badFilter;
  }
  start?.addEventListener("change", valid);
  end?.addEventListener("change", valid);
  filter?.addEventListener("change", valid);
  form.addEventListener("submit", (event) => {
    if (!valid()) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
});
