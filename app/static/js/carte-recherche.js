"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const carte = L.map("carte-recherche").setView([46.8139, -71.208], 12);
  
  requestAnimationFrame(() => {
      carte.invalidateSize();
  });

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(carte);

  const formulaire = document.getElementById("research");
  const liste = document.getElementById("liste-stationnements");
  const compteur = document.getElementById("nb_results");
  const message = document.getElementById("carte-message");

  const selectVille = formulaire.querySelector('[name="ville"]');

  const centresVilles = {
    Montréal: [45.5019, -73.5674],
    Québec: [46.8139, -71.208],
    Laval: [45.6066, -73.7124],
    Gatineau: [45.4765, -75.7013],
    Longueuil: [45.5312, -73.5181],
    Sherbrooke: [45.4042, -71.8929],
    Lévis: [46.7382, -71.2465],
    Saguenay: [48.4281, -71.0688],
    "Trois-Rivières": [46.3432, -72.543],
    Terrebonne: [45.7005, -73.6478],
    "Saint-Jean-sur-Richelieu": [45.3071, -73.2626],
    Brossard: [45.4675, -73.4512],
    Repentigny: [45.7422, -73.4501],
    "Saint-Jérôme": [45.7804, -74.0036],
    Drummondville: [45.8834, -72.4843],
  };

  const coucheMarqueurs = L.layerGroup().addTo(carte);

  let marqueurs = new Map();
  let timer = null;
  let requeteEnCours = null;
  let numeroRequete = 0;

  function lireFiltres() {
    return {
      ville: formulaire?.querySelector('[name="ville"]')?.value || "",
      filter: formulaire?.querySelector('[name="filter"]')?.value || "Tous",
      debut: formulaire?.querySelector('[name="debut"]')?.value || "",
      fin: formulaire?.querySelector('[name="fin"]')?.value || "",
    };
  }

  function creerCarteAnnonce(item) {
    const article = document.createElement("article");
    article.className = "list-group-item mb-2 rounded border";

    const contenu = document.createElement("div");
    contenu.className = "d-flex gap-3 align-items-start";

    const image = document.createElement("img");
    image.className = "rounded";
    image.style.width = "115px";
    image.style.height = "100px";
    image.style.objectFit = "cover";
    image.alt = "Photo du stationnement";
    image.src = item.img
      ? `/static/img/stationnement/${encodeURIComponent(item.img)}`
      : "/static/img/placeholder.jpg";

    const details = document.createElement("div");
    details.className = "flex-grow-1";

    const titre = document.createElement("h6");
    titre.className = "fw-bold mb-1";
    titre.textContent = item.address;

    const ville = document.createElement("p");
    ville.className = "small text-muted mb-1";
    ville.textContent = `${item.city} — ${item.location}`;

    const prix = document.createElement("p");
    prix.className = "fw-bold mb-2";
    prix.textContent = `${Number(item.price).toFixed(2)} $/h`;

    const boutons = document.createElement("div");
    boutons.className = "d-flex flex-wrap gap-2";

    const voirCarte = document.createElement("button");
    voirCarte.type = "button";
    voirCarte.className = "btn btn-sm btn-outline-dark";
    voirCarte.textContent = "Voir sur la carte";

    voirCarte.addEventListener("click", () => {
      const marqueur = marqueurs.get(item.id);

      if (!marqueur) return;

      carte.flyTo(marqueur.getLatLng(), Math.max(carte.getZoom(), 16));
      marqueur.openPopup();
    });

    const detailsLien = document.createElement("a");
    detailsLien.className = "btn btn-sm btn-dark";
    detailsLien.href = `/stationnement/detail/${item.id}`;
    detailsLien.textContent = "Détails";

    boutons.append(voirCarte, detailsLien);
    details.append(titre, ville, prix, boutons);
    contenu.append(image, details);
    article.append(contenu);

    return article;
  }

  function creerMarqueur(item) {
    const prix = Number(item.price).toFixed(2);

    const icone = L.divIcon({
      className: "parkshare-marker-container",
      html: `<span class="parkshare-price">${prix} $/h</span>`,
      iconSize: [90, 34],
      iconAnchor: [45, 17],
    });

    const marqueur = L.marker([item.latitude, item.longitude], { icon: icone });

    const popup = document.createElement("div");

    const titre = document.createElement("strong");
    titre.textContent = item.address;

    const prixElement = document.createElement("p");
    prixElement.textContent = `${prix} $/heure`;

    const lien = document.createElement("a");
    lien.href = `/stationnement/detail/${item.id}`;
    lien.textContent = "Voir la publication";

    popup.append(titre, prixElement, lien);
    marqueur.bindPopup(popup);

    return marqueur;
  }

  function afficherResultats(publications) {
    liste.replaceChildren();
    coucheMarqueurs.clearLayers();
    marqueurs.clear();

    compteur.textContent = publications.length;

    if (publications.length === 0) {
      const vide = document.createElement("p");
      vide.className = "text-muted p-3";
      vide.textContent = "Aucun stationnement disponible dans cette zone.";
      liste.append(vide);
    }

    for (const item of publications) {
      liste.append(creerCarteAnnonce(item));

      const marqueur = creerMarqueur(item);
      marqueur.addTo(coucheMarqueurs);
      marqueurs.set(item.id, marqueur);
    }

    message.textContent = `${publications.length} stationnement(s) dans la zone visible.`;
  }

  async function chargerStationnements() {
    const bounds = carte.getBounds();
    const filtres = lireFiltres();
    mettreAJourURL();

    if (requeteEnCours) {
      requeteEnCours.abort();
    }

    const controller = new AbortController();
    requeteEnCours = controller;
    const idRequete = ++numeroRequete;

    const params = new URLSearchParams({
      south: bounds.getSouth().toString(),
      north: bounds.getNorth().toString(),
      west: bounds.getWest().toString(),
      east: bounds.getEast().toString(),
      ville: filtres.ville,
      filter: filtres.filter,
      debut: filtres.debut,
      fin: filtres.fin,
    });

    message.textContent = "Recherche des stationnements...";

    try {
      const response = await fetch(
        `/api/publications/map?${params.toString()}`,
        { signal: controller.signal },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Erreur de recherche");
      }

      if (idRequete !== numeroRequete) return;

      afficherResultats(data);
    } catch (error) {
      if (error.name === "AbortError") return;
      if (idRequete !== numeroRequete) return;

      message.textContent = error.message;
    } finally {
      if (requeteEnCours === controller) {
        requeteEnCours = null;
      }
    }
  }

  const paramsURL = new URLSearchParams(window.location.search);

  for (const nom of ["ville", "filter", "debut", "fin"]) {
    const champ = formulaire.querySelector(`[name="${nom}"]`);
    const valeur = paramsURL.get(nom);

    if (champ && valeur !== null) {
      champ.value = valeur;
    }
  }

  const centreInitial = centresVilles[selectVille.value];

  if (centreInitial) {
    carte.setView(centreInitial, 12, { animate: false });
  }

  function planifierRecherche() {
    clearTimeout(timer);
    timer = setTimeout(chargerStationnements, 250);
  }

  carte.on("moveend", planifierRecherche);

  formulaire
    ?.querySelector('[name="filter"]')
    ?.addEventListener("change", planifierRecherche);

  formulaire
    ?.querySelectorAll('[name="debut"], [name="fin"]')
    .forEach((champ) => {
      champ.addEventListener("change", planifierRecherche);
    });

  formulaire?.addEventListener("submit", (event) => {
    event.preventDefault();

    const centre = centresVilles[selectVille.value];

    if (centre) {
      carte.setView(centre, 12, { animate: false });
    }

    planifierRecherche();
  });

  selectVille.addEventListener("change", () => {
    const centre = centresVilles[selectVille.value];

    if (centre) {
      carte.setView(centre, 12, { animate: false });
    }

    planifierRecherche();
  });

  chargerStationnements();

  function mettreAJourURL() {
    const filtres = lireFiltres();
    const url = new URL(window.location.href);

    for (const [cle, valeur] of Object.entries(filtres)) {
      if (valeur && valeur !== "Tous") {
        url.searchParams.set(cle, valeur);
      } else {
        url.searchParams.delete(cle);
      }
    }

    window.history.replaceState(null, "", url);
  }

});