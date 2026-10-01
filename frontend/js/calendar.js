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

    const titel = document.getElementById("termin-titel").value;
    const datum = document.getElementById("termin-datum").value;
    const uhrzeit = document.getElementById("termin-uhrzeit").value;
    const start = `${datum}T${uhrzeit}`;

    terminStatus.textContent = "Termin wird angelegt...";

    try {
        const response = await fetch("http://127.0.0.1:8000/kalender/termin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ titel, start })
        });

        if (!response.ok) {
            throw new Error("Termin konnte nicht angelegt werden.");
        }

        terminStatus.textContent = "Termin angelegt: " + titel;
        terminFormular.reset();
        terminFormular.hidden = true;
        terminToggle.textContent = "+ Neuer Termin";
        calendarButton.click(); // Liste neu laden

    } catch (error) {
        console.error(error);
        terminStatus.textContent = "Fehler beim Anlegen des Termins.";
    }
});