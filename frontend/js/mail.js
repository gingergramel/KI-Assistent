async function loadMails() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/mails");

        const mails = await response.json();

        const container = document.getElementById("mail-list");

        container.innerHTML = "";

        mails.forEach(mail => {
            const mailElement = document.createElement("div");

            mailElement.classList.add("mail-box");

            mailElement.innerHTML = `
                <div class="mail-sender">${mail.from}</div>
                <div class="mail-subject">${mail.subject}</div>
                <div class="mail-snippet">${mail.snippet}</div>
                <div class="mail-date">${mail.date}</div>
            `;

            container.appendChild(mailElement);
        });

    } catch (error) {
        console.error("Fehler beim Laden der Mails:", error);
    }
}

loadMails();