"use strict";

const form = document.getElementById('ajout_form');
const dateDebut = document.getElementById("dateDebut");
const dateFin = document.getElementById("dateFin");
const msgFin = document.getElementById("msgFin");

function validerDateFin() {

    const minimum = new Date(dateDebut.value);
    minimum.setMinutes(minimum.getMinutes() + 30);

    const fin = new Date(dateFin.value);

    if (fin < minimum) {
        dateFin.classList.add("is-invalid");
        msgFin.textContent =
            "La date de fin doit être supérieur 30 minutes minimum.";
    } else {
        dateFin.classList.remove("is-invalid");
        dateFin.nextElementSibling.textContent = "";
    }
}

function envoyerForm(e) {

    validerDateFin();
    if (dateFin.classList.contains("is-invalid")) {
        e.preventDefault();
    }
}

function initialisation() {

    const maintenant = new Date();
    maintenant.setMinutes(maintenant.getMinutes() - maintenant.getTimezoneOffset());
    const strDebut = maintenant.toISOString().slice(0, 16);
    dateDebut.value = strDebut;
    dateDebut.min = strDebut;
    dateDebut.readOnly = true;

    const fin = new Date();
    fin.setMinutes(fin.getMinutes() + 30);
    fin.setMinutes(fin.getMinutes() - fin.getTimezoneOffset());
    dateFin.value = fin.toISOString().slice(0, 16);
    dateFin.min = fin.toISOString().slice(0, 16);


    dateFin.addEventListener("blur", validerDateFin);
    form.addEventListener("submit", envoyerForm);
}

window.addEventListener("load", initialisation);