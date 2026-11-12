const KALENDER_URL = "http://127.0.0.1:8000/kalender";

const calendarButton = document.getElementById("calendarButton");
const calendarOutput = document.getElementById("calendarOutput");

const terminToggle = document.getElementById("termin-toggle");
const terminFormular = document.getElementById("termin-formular");
const terminStatus = document.getElementById("termin-status");
const terminSpeichernButton = terminFormular.querySelector('button[type="submit"]');

// Wenn gesetzt, ändert das Formular diesen Termin, statt einen neuen anzulegen
let bearbeiteterTermin = null;

// Die geladenen Termine, auch die Monatsansicht (kalender-ansicht.js) liest sie von hier
window.kalenderTermine = [];


// ===== Hilfsfunktionen =====

function zweistellig(zahl) {
    return String(zahl).padStart(2, "0");
}

function istGanztaegig(termin) {
    return !termin.start.includes("T");
}

function datumFuerFeld(datum) {
    return `${datum.getFullYear()}-${zweistellig(datum.getMonth() + 1)}-${zweistellig(datum.getDate())}`;
}

function zeitFuerFeld(datum) {
    return `${zweistellig(datum.getHours())}:${zweistellig(datum.getMinutes())}`;
}

function uhrzeitAnzeige(datum) {
    return datum.toLocaleTimeString("de-AT", { hour: "2-digit", minute: "2-digit" });
}

function konfliktText(konflikte) {
    if (!konflikte || konflikte.length === 0) {
        return "";
    }

    const teile = konflikte.map((konflikt) => {
        const von = uhrzeitAnzeige(new Date(konflikt.start));
        const bis = uhrzeitAnzeige(new Date(konflikt.end));
        const name = konflikt.titel ? konflikt.titel + " " : "";
        return `${name}(${von}–${bis})`;
    });

    return " Belegt: " + teile.join(", ");
}


// ===== Termine anzeigen =====

function baueTerminAktionen(termin) {
    const box = document.createElement("div");
    box.classList.add("termin-aktionen");

    // Ganztägige Termine lassen sich nur löschen, die Zeiten kann man dort nicht ändern
    if (!istGanztaegig(termin)) {
        const bearbeiten = document.createElement("button");
        bearbeiten.type = "button";
        bearbeiten.classList.add("aktion-button");
        bearbeiten.textContent = "Bearbeiten";
        bearbeiten.addEventListener("click", () => starteBearbeitung(termin));
        box.appendChild(bearbeiten);
    }

    const loeschen = document.createElement("button");
    loeschen.type = "button";
    loeschen.classList.add("aktion-button", "loeschen");
    loeschen.textContent = "Löschen";
    loeschen.addEventListener("click", () => loescheTermin(termin));
    box.appendChild(loeschen);

    return box;
}

// Die Monatsansicht nutzt dieselben Schaltflächen
window.baueTerminAktionen = baueTerminAktionen;

function baueTerminKarte(termin) {
    const karte = document.createElement("div");
    karte.classList.add("calendar-event");

    const titel = document.createElement("div");
    titel.classList.add("calendar-event-title");
    titel.textContent = termin.titel;

    const datumZeile = document.createElement("div");
    datumZeile.classList.add("calendar-event-date");

    const zeitZeile = document.createElement("div");
    zeitZeile.classList.add("calendar-event-time");

    if (istGanztaegig(termin)) {
        const [jahr, monat, tag] = termin.start.split("-").map(Number);
        datumZeile.textContent = "📅 " + new Date(jahr, monat - 1, tag).toLocaleDateString("de-AT");
        zeitZeile.textContent = "🕒 ganztägig";
    } else {
        const start = new Date(termin.start);
        const ende = new Date(termin.ende);
        datumZeile.textContent = "📅 " + start.toLocaleDateString("de-AT");
        zeitZeile.textContent = "🕒 " + uhrzeitAnzeige(start) + " – " + uhrzeitAnzeige(ende);
    }

    karte.append(titel, datumZeile, zeitZeile, baueTerminAktionen(termin));
    return karte;
}

async function ladeTermine() {
    calendarOutput.textContent = "Termine werden geladen...";

    try {
        const response = await fetch(KALENDER_URL);

        if (!response.ok) {
            throw new Error("Kalender konnte nicht geladen werden.");
        }

        const data = await response.json();
        window.kalenderTermine = data.termine || [];

        calendarOutput.innerHTML = "";

        if (window.kalenderTermine.length === 0) {
            calendarOutput.textContent = "Keine kommenden Termine gefunden.";
        } else {
            window.kalenderTermine.forEach((termin) => {
                calendarOutput.appendChild(baueTerminKarte(termin));
            });
        }

        // Sagt der Monatsansicht, dass es neue Daten gibt
        document.dispatchEvent(new CustomEvent("termine-geladen"));

    } catch (error) {
        console.error(error);
        calendarOutput.textContent = "Fehler beim Laden der Termine.";
    }
}

calendarButton.addEventListener("click", ladeTermine);


// ===== Formular: neuer Termin oder Änderung =====

function formularSchliessen() {
    bearbeiteterTermin = null;
    terminFormular.reset();
    terminFormular.hidden = true;
    terminToggle.textContent = "+ Neuer Termin";
    terminSpeichernButton.textContent = "Termin anlegen";
}

terminToggle.addEventListener("click", () => {
    if (!terminFormular.hidden) {
        formularSchliessen();
    } else {
        terminStatus.textContent = "";
        terminFormular.hidden = false;
        terminToggle.textContent = "– Formular schließen";
    }
});

function starteBearbeitung(termin) {
    const start = new Date(termin.start);
    const ende = new Date(termin.ende);

    bearbeiteterTermin = {
        id: termin.id,
        titel: termin.titel,
        datum: datumFuerFeld(start),
        startzeit: zeitFuerFeld(start),
        endzeit: zeitFuerFeld(ende)
    };

    document.getElementById("termin-titel").value = bearbeiteterTermin.titel;
    document.getElementById("termin-datum").value = bearbeiteterTermin.datum;
    document.getElementById("termin-uhrzeit").value = bearbeiteterTermin.startzeit;
    document.getElementById("termin-endzeit").value = bearbeiteterTermin.endzeit;

    terminFormular.hidden = false;
    terminToggle.textContent = "– Bearbeitung abbrechen";
    terminSpeichernButton.textContent = "Änderung speichern";
    terminStatus.textContent = "Termin bearbeiten: " + termin.titel;

    terminFormular.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function legeTerminAn(titel, datum, startzeit, dauer_minuten) {
    terminStatus.textContent = "Kalender wird auf freie Termine überprüft...";

    try {
        const response = await fetch(KALENDER_URL + "/termin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                titel: titel,
                start: `${datum}T${startzeit}`,
                dauer_minuten: dauer_minuten
            })
        });

        const data = await response.json();

        if (!response.ok) {
            terminStatus.textContent = "Serverfehler: " + JSON.stringify(data.detail || data);
            return;
        }

        // Zeitraum ist belegt, oder der Termin steht schon so im Kalender
        if (data.erstellt === false) {
            terminStatus.textContent = "⚠️ " + data.nachricht + konfliktText(data.konflikte);
            return;
        }

        if (data.erstellt === true) {
            // Gab es den Namen an dem Tag schon, wurde der vorhandene Termin verschoben
            terminStatus.textContent = data.aktualisiert
                ? "🔁 " + data.nachricht
                : "✅ Termin erfolgreich angelegt: " + titel;
            formularSchliessen();
            ladeTermine();
            return;
        }

        terminStatus.textContent = "Unerwartete Antwort vom Backend.";

    } catch (error) {
        console.error("Kalenderfehler:", error);
        terminStatus.textContent = "Fehler beim Anlegen des Termins: " + error.message;
    }
}

async function speichereAenderung(titel, datum, startzeit, endzeit, dauer_minuten) {
    const alt = bearbeiteterTermin;
    const aenderung = {};

    // Nur schicken, was sich wirklich geändert hat
    if (titel !== alt.titel) {
        aenderung.titel = titel;
    }

    const zeitGeaendert =
        datum !== alt.datum || startzeit !== alt.startzeit || endzeit !== alt.endzeit;

    if (zeitGeaendert) {
        aenderung.start = `${datum}T${startzeit}`;
        aenderung.dauer_minuten = dauer_minuten;
    }

    if (Object.keys(aenderung).length === 0) {
        terminStatus.textContent = "Es wurde nichts geändert.";
        return;
    }

    terminStatus.textContent = "Änderung wird gespeichert...";

    try {
        const response = await fetch(`${KALENDER_URL}/termin/${encodeURIComponent(alt.id)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(aenderung)
        });

        const data = await response.json();

        if (!response.ok) {
            terminStatus.textContent = "Serverfehler: " + JSON.stringify(data.detail || data);
            return;
        }

        // Neuer Zeitraum ist belegt oder der Name kommt an dem Tag schon vor, im Kalender bleibt alles beim Alten
        if (data.geaendert === false) {
            terminStatus.textContent = "⚠️ " + data.nachricht + konfliktText(data.konflikte);
            return;
        }

        terminStatus.textContent = "✅ Termin geändert: " + (data.titel || titel);
        formularSchliessen();
        ladeTermine();

    } catch (error) {
        console.error("Kalenderfehler:", error);
        terminStatus.textContent = "Fehler beim Ändern des Termins: " + error.message;
    }
}

terminFormular.addEventListener("submit", async (e) => {
    e.preventDefault();

    const titel = document.getElementById("termin-titel").value.trim();
    const datum = document.getElementById("termin-datum").value;
    const startzeit = document.getElementById("termin-uhrzeit").value;
    const endzeit = document.getElementById("termin-endzeit").value;

    const start = new Date(`${datum}T${startzeit}`);
    const ende = new Date(`${datum}T${endzeit}`);

    // Prüfen, ob die Uhrzeiten gültig sind
    if (Number.isNaN(start.getTime()) || Number.isNaN(ende.getTime())) {
        terminStatus.textContent = "Ungültiges Datum oder Uhrzeit.";
        return;
    }

    // Endzeit muss nach Startzeit liegen
    if (ende <= start) {
        terminStatus.textContent = "Die Endzeit muss nach der Startzeit liegen.";
        return;
    }

    // Dauer in Minuten berechnen
    const dauer_minuten = Math.round((ende - start) / (1000 * 60));

    if (bearbeiteterTermin) {
        await speichereAenderung(titel, datum, startzeit, endzeit, dauer_minuten);
    } else {
        await legeTerminAn(titel, datum, startzeit, dauer_minuten);
    }
});


// ===== Termin löschen =====

async function loescheTermin(termin) {
    if (!confirm(`Termin „${termin.titel}“ wirklich löschen?`)) {
        return;
    }

    terminStatus.textContent = "Termin wird gelöscht...";

    try {
        const response = await fetch(`${KALENDER_URL}/termin/${encodeURIComponent(termin.id)}`, {
            method: "DELETE"
        });

        if (!response.ok) {
            let grund = "";
            try {
                const fehlerDaten = await response.json();
                grund = fehlerDaten.detail || "";
            } catch (e) {
                // Antwort war kein JSON
            }
            terminStatus.textContent = "Fehler beim Löschen: " + grund;
            return;
        }

        terminStatus.textContent = "🗑️ Termin gelöscht: " + termin.titel;

        // Wurde gerade genau dieser Termin bearbeitet, das Formular schließen
        if (bearbeiteterTermin && bearbeiteterTermin.id === termin.id) {
            formularSchliessen();
        }

        ladeTermine();

    } catch (error) {
        console.error("Kalenderfehler:", error);
        terminStatus.textContent = "Fehler beim Löschen des Termins: " + error.message;
    }
}