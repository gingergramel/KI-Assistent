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