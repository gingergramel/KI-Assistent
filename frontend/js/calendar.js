const calendarButton = document.getElementById("calendarButton");
const calendarOutput = document.getElementById("calendarOutput");

calendarButton.addEventListener("click", async () => {
    calendarOutput.textContent = "Termine werden geladen...";

    try {
        const response = await fetch("http://127.0.0.1:8000/kalender");

        if (!response.ok) {
            throw new Error("Kalender konnte nicht geladen werden.");
        }

        const data = await response.json();

        calendarOutput.innerHTML = "";

        if (!data.termine || data.termine.length === 0) {
            calendarOutput.textContent = "Keine kommenden Termine gefunden.";
            return;
        }

        data.termine.forEach((termin) => {
            const div = document.createElement("div");
            div.classList.add("calendar-event");

            const datum = new Date(termin.start);

            div.innerHTML = `
                <div class="calendar-event-title">${termin.titel}</div>

                <div class="calendar-event-date">
                    📅 ${datum.toLocaleDateString("de-AT")}
                </div>

                <div class="calendar-event-time">
                    🕒 ${datum.toLocaleTimeString("de-AT", {
                        hour: "2-digit",
                        minute: "2-digit"
                    })}
                </div>
            `;

            calendarOutput.appendChild(div);
        });

    } catch (error) {
        console.error(error);
        calendarOutput.textContent = "Fehler beim Laden der Termine.";
    }
});

const terminToggle = document.getElementById("termin-toggle");
const terminFormular = document.getElementById("termin-formular");
const terminStatus = document.getElementById("termin-status");

terminToggle.addEventListener("click", () => {
  const istOffen = !terminFormular.hidden;
  terminFormular.hidden = istOffen;
  terminToggle.textContent = istOffen ? "+ Neuer Termin" : "– Formular schließen";
});


terminFormular.addEventListener("submit", async (e) => {
    e.preventDefault();

    const titel = document.getElementById("termin-titel").value.trim();
    const datum = document.getElementById("termin-datum").value;
    const startzeit = document.getElementById("termin-uhrzeit").value;
    const endzeit = document.getElementById("termin-endzeit").value;

    const start = new Date(`${datum}T${startzeit}`);
    const ende = new Date(`${datum}T${endzeit}`);

    // Prüfen, ob die Uhrzeiten gültig sind
    if (
        Number.isNaN(start.getTime()) ||
        Number.isNaN(ende.getTime())
    ) {
        terminStatus.textContent = "Ungültiges Datum oder Uhrzeit.";
        return;
    }

    // Endzeit muss nach Startzeit liegen
    if (ende <= start) {
        terminStatus.textContent =
            "Die Endzeit muss nach der Startzeit liegen.";
        return;
    }

    // Dauer in Minuten berechnen
    const dauer_minuten = Math.round(
        (ende - start) / (1000 * 60)
    );

    terminStatus.textContent =
        "Kalender wird auf freie Termine überprüft...";

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/kalender/termin",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    titel: titel,
                    start: `${datum}T${startzeit}`,
                    dauer_minuten: dauer_minuten
                })
            }
        );

        const data = await response.json();

        console.log("Kalender-Antwort:", data);

        if (!response.ok) {
            terminStatus.textContent =
                "Serverfehler: " +
                JSON.stringify(data.detail || data);
            return;
        }

        // Zeitraum ist bereits belegt
        if (data.erstellt === false) {
            terminStatus.textContent =
                "⚠️ " + data.nachricht;
            return;
        }

        // Termin wurde erstellt
        if (data.erstellt === true) {
            terminStatus.textContent =
                "✅ Termin erfolgreich angelegt: " + titel;

            terminFormular.reset();
            terminFormular.hidden = true;
            terminToggle.textContent = "+ Neuer Termin";

            calendarButton.click();
            return;
        }

        terminStatus.textContent =
            "Unerwartete Antwort vom Backend.";

    } catch (error) {
        console.error("Kalenderfehler:", error);

        terminStatus.textContent =
            "Fehler beim Anlegen des Termins: " +
            error.message;
    }
});
