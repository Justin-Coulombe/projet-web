"use strict";
// Validation Bootstrap + envoi AJAX commun pour 7 formulaires ParkShare.
document.addEventListener("DOMContentLoaded", () => {
  const RULES = {
    login: ["email", "password"],
    register: ["prenom", "nom", "email", "password", "password_confirm"],
    profile: ["prenom", "nom", "email"],
    password: ["current_password", "new_password", "confirm_password"],
    parking: ["adresse", "ville", "prix", "place", "emplacement", "dateDebut", "dateFin", "geocode_token", "image"],
    "parking-edit": ["adresse", "ville", "prix", "place", "emplacement", "dateDebut", "dateFin", "geocode_token"],
    image: ["image"],
    delete: [],
    logout: []
  };
  const getInput = (form, name) => [...form.elements].find(el => el.name === name);
  const value = (form, name) => (getInput(form, name)?.value ?? "").trim();
  const csrf = () => document.querySelector('meta[name="csrf-token"]')?.content || "";

  function errorFor(form, name, kind) {
    const input = getInput(form, name);
    if (!input) return "";
    const v = value(form, name);
    if (["prenom", "nom"].includes(name)) {
      return v.length >= 2 && v.length <= 80 && /^[\p{L} '-]+$/u.test(v)
        ? "" : "Entre 2 et 80 caractères : lettres et tirets uniquement.";
    }
    if (name === "email") return /^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$/.test(v) && v.length <= 254
      ? "" : "Entrez une adresse courriel valide.";
    if (["password", "new_password"].includes(name)) {
      if (kind === "login") return v ? "" : "Mot de passe obligatoire.";
      return v.length >= 8 && v.length <= 128 ? "" : "Entre 8 et 128 caractères.";
    }
    if (name === "current_password") return v ? "" : "Entrez votre mot de passe actuel.";
    if (["password_confirm", "confirm_password"].includes(name)) {
      const other = name === "password_confirm" ? "password" : "new_password";
      return v === value(form, other) && v ? "" : "Les mots de passe ne correspondent pas.";
    }
    if (name === "adresse") return v.length >= 5 && v.length <= 200 ? "" : "Adresse requise (5 à 200 caractères).";
    if (name === "ville") return v ? "" : "Sélectionnez une ville.";
    if (name === "emplacement") return ["Intérieur", "Extérieur"].includes(v) ? "" : "Choisissez un type valide.";
    if (name === "prix") {
      const x = Number(v);
      return v && /^\d+(?:\.\d{1,2})?$/.test(v) && Number.isFinite(x) && x >= 0.01 && x <= 1000
        ? "" : "Prix entre 0,01 $ et 1 000 $, avec 2 décimales maximum.";
    }
    if (name === "place") return /^\d{1,3}$/.test(v) && +v >= 1 && +v <= 100
      ? "" : "Entrez un entier entre 1 et 100.";
    if (name === "dateDebut") return !v || Number.isNaN(new Date(v).getTime())
      ? "Date de début obligatoire." : "";
    if (name === "dateFin") {
      const a = new Date(value(form, "dateDebut")), b = new Date(v);
      return !v || Number.isNaN(b.getTime()) || Number.isNaN(a.getTime()) || (b - a) < 30 * 60 * 1000
        ? "La fin doit suivre le début d'au moins 30 minutes." : "";
    }
    if (name === "geocode_token") {
      if (kind === "parking-edit") {
        const same = value(form, "adresse") === (form.dataset.originalAdresse || "").trim()
          && value(form, "ville") === (form.dataset.originalVille || "").trim();
        if (same && form.dataset.hasCoordinates === "true") return "";
      }
      return v ? "" : "Vérifiez l'adresse sur la carte avant d'enregistrer.";
    }
    if (name === "image") {
      const file = input.files?.[0];
      if (!file) return kind === "parking" || kind === "image" ? "Sélectionnez une photo." : "";
      if (file.size > 2 * 1024 * 1024) return "La photo ne peut pas dépasser 2 Mo.";
      if (!["image/jpeg", "image/png", "image/webp"].includes(file.type))
        return "Formats autorisés : JPEG, PNG et WebP.";
      return "";
    }
    return "";
  }

  function applyMessage(form, name, message, success = true) {
    const input = getInput(form, name);
    if (!input) return;
    // Jeton masqué : erreur affichée sur la zone de géocodage.
    if (name === "geocode_token") {
      const node = form.querySelector("#geocode-status");
      if (node) {
        node.textContent = message || node.textContent;
        if (message) node.className = "small text-danger mt-2";
      }
      const addressInput = getInput(form, "adresse");
      if (message && addressInput) addressInput.classList.add("is-invalid");
      return;
    }
    input.classList.toggle("is-invalid", Boolean(message));
    input.classList.toggle("is-valid", !message && success && input.type !== "file");
    input.setAttribute("aria-invalid", String(Boolean(message)));
    let feedback = form.querySelector(`[data-validation-for="${name}"]`);
    if (!feedback) {
      feedback = document.createElement("div");
      feedback.dataset.validationFor = name;
      feedback.className = "invalid-feedback d-block";
      const wrapper = input.closest(".auth-password, .auth-input, .input-group") || input;
      wrapper.insertAdjacentElement("afterend", feedback);
    }
    feedback.textContent = message || "";
  }

  function validate(form, kind, showAll = false) {
    const errors = {};
    for (const name of RULES[kind] || []) {
      const e = errorFor(form, name, kind);
      if (e) errors[name] = e;
      if (showAll || getInput(form, name)?.dataset.touched) applyMessage(form, name, e);
    }
    return errors;
  }

  for (const form of document.querySelectorAll("form[data-ajax-form]")) {
    const kind = form.dataset.ajaxForm;
    if (!Object.hasOwn(RULES, kind)) continue;
    form.noValidate = true;
    for (const input of form.querySelectorAll("input, select")) {
      if (!input.name) continue;
      const check = () => {
        input.dataset.touched = "true";
        applyMessage(form, input.name, errorFor(form, input.name, kind));
        if (["password", "new_password", "dateDebut"].includes(input.name)) {
          const dependent = { password: "password_confirm", new_password: "confirm_password", dateDebut: "dateFin" }[input.name];
          if (getInput(form, dependent)?.dataset.touched) {
            applyMessage(form, dependent, errorFor(form, dependent, kind));
          }
        }
      };
      input.addEventListener("blur", check);
      input.addEventListener("input", check);
      input.addEventListener("change", check);
    }
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) return;
      const errors = validate(form, kind, true);
      if (Object.keys(errors).length) {
        const first = Object.keys(errors).find(n => getInput(form, n)?.type !== "hidden");
        getInput(form, first)?.focus();
        return;
      }
      const button = form.querySelector('[type="submit"]');
      const previousText = button?.textContent;
      if (button) { button.disabled = true; button.textContent = "Enregistrement..."; }
      form.querySelectorAll("[data-form-alert]").forEach(n => n.remove());
      try {
        const response = await fetch(form.action, {
          method: form.method || "POST",
          headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrf() },
          credentials: "same-origin",
          body: new FormData(form)
        });
        const result = await response.json();
        if (!response.ok || !result.ok) {
          for (const [name, msg] of Object.entries(result.errors || {})) {
            applyMessage(form, name, msg);
          }
          const alert = document.createElement("div");
          alert.dataset.formAlert = "";
          alert.className = "alert alert-danger";
          alert.role = "alert";
          alert.textContent = result.errors?._form || "Corrigez les champs indiqués.";
          form.prepend(alert);
          return;
        }
        if (result.redirect) window.location.assign(result.redirect);
      } catch (err) {
        const alert = document.createElement("div");
        alert.dataset.formAlert = "";
        alert.className = "alert alert-danger";
        alert.textContent = "Erreur réseau. Réessayez sans perdre vos données.";
        form.prepend(alert);
      } finally {
        if (button) { button.disabled = false; button.textContent = previousText; }
      }
    });
  }
});
