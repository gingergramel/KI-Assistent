const mailButton = document.getElementById("mailButton");
const mailOutput = document.getElementById("mail-list");

mailButton.addEventListener("click", async () => {
    mailOutput.textContent = "Mails werden geladen...";

    try {
        const response = await fetch("http://127.0.0.1:8000/api/mails");

        if (!response.ok) {
            throw new Error("Mails konnten nicht geladen werden.");
        }

        const mails = await response.json();

        mailOutput.innerHTML = "";

        if (!mails || mails.length === 0) {
            mailOutput.textContent = "Keine Mails gefunden.";
            return;
        }

        const lastFiveMails = mails.slice(0, 5);

        lastFiveMails.forEach((mail) => {
            const div = document.createElement("div");

            div.classList.add("mail-box");

            div.innerHTML = `
                <div class="mail-sender">${mail.from}</div>
                <div class="mail-subject">${mail.subject}</div>
                <div class="mail-snippet">${mail.snippet}</div>
                <div class="mail-date">${mail.date}</div>
            `;

            mailOutput.appendChild(div);
        });

    } catch (error) {
        console.error(error);
        mailOutput.textContent = "Fehler beim Laden der Mails.";
    }
});