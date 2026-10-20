"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const formulaire = document.getElementById("ajout_form");
  const adresse = document.getElementById("adresse");
  const ville = document.getElementById("ville");

  const bouton = document.getElementById("verifier-adresse");
  const statut = document.getElementById("geocode-status");
  const token = document.getElementById("geocode-token");

  const apercu = document.getElementById("geocode-preview");
  const adresseReconnue = document.getElementById("adresse-reconnue");

  if (!formulaire || !adresse || !ville || !bouton) {
    return;
  }

  let carte = null;
  let marqueur = null;
  let numeroRecherche = 0;

  function invaliderAdresse() {
    numeroRecherche++;
    token.value = "";
    apercu.hidden = true;
    statut.textContent = "";
  }

  adresse.addEventListener("input", invaliderAdresse);
  ville.addEventListener("change", invaliderAdresse);

  function afficherPosition(latitude, longitude) {
    apercu.hidden = false;

    if (carte === null) {
      carte = L.map("geocode-map").setView([latitude, longitude], 17);

      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(carte);

      marqueur = L.marker([latitude, longitude]).addTo(carte);
    } else {
      carte.setView([latitude, longitude], 17);
      marqueur.setLatLng([latitude, longitude]);
    }

    requestAnimationFrame(() => {
      carte.invalidateSize();
    });
  }

  bouton.addEventListener("click", async () => {
    const valeurAdresse = adresse.value.trim();
    const valeurVille = ville.value.trim();

    invaliderAdresse();

    if (!valeurAdresse || !valeurVille) {
      statut.textContent = "Entrez une adresse et sélectionnez une ville.";
      statut.className = "text-danger small mt-2";
      return;
    }

    const rechercheActive = numeroRecherche;

    bouton.disabled = true;
    bouton.textContent = "Vérification en cours...";
    statut.textContent = "Recherche de l'adresse...";
    statut.className = "text-muted small mt-2";

    try {
      const reponse = await fetch("/api/geocode", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.content || "",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          adresse: valeurAdresse,
          ville: valeurVille,
        }),
      });

      const data = await reponse.json();

      if (rechercheActive !== numeroRecherche) {
        return;
      }

      if (!reponse.ok || !data.success) {
        throw new Error(data.message || "Adresse non trouvée.");
      }

      token.value = data.token;
      adresseReconnue.textContent = data.adresse_complete;

      afficherPosition(data.latitude, data.longitude);

      statut.textContent =
        "Adresse géolocalisée. Vérifiez le repère sur la carte.";
      statut.className = "text-success small mt-2";
    } catch (erreur) {
      if (rechercheActive === numeroRecherche) {
        token.value = "";
        apercu.hidden = true;
        statut.textContent = erreur.message;
        statut.className = "text-danger small mt-2";
      }
    } finally {
      bouton.disabled = false;
      bouton.textContent = "Vérifier l'adresse";
    }
  });

  const nouvelleAnnonce = formulaire.action.includes("/stationnement/ajouter");

  formulaire.addEventListener("submit", (event) => {
    if (nouvelleAnnonce && !token.value) {
      event.preventDefault();

      statut.textContent = "Vérifiez votre adresse avant de publier.";
      statut.className = "text-danger small mt-2";
    }
  });
});
