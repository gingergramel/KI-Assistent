const CHAT_URL = "http://127.0.0.1:8000/chat";

// Eine Sitzungs-ID pro Seitenaufruf, damit Gemini sich an das Gespräch erinnert
const chatSessionId = Date.now() + "-" + Math.random().toString(36).slice(2);

let chatWartetAufAntwort = false;

function fuegeChatNachrichtHinzu(text, absender) {
  const verlauf = document.getElementById("chat-verlauf");
  const nachricht = document.createElement("div");
  nachricht.classList.add("chat-nachricht", absender);
  nachricht.textContent = text;
  verlauf.appendChild(nachricht);
  verlauf.scrollTop = verlauf.scrollHeight;
  return nachricht;
}

async function sendeChatNachricht() {
  if (chatWartetAufAntwort) return;

  const eingabeFeld = document.getElementById("chat-eingabe");
  const sendenBtn = document.getElementById("chat-senden-btn");
  const verlauf = document.getElementById("chat-verlauf");

  const text = eingabeFeld.value.trim();
  if (!text) return;

  fuegeChatNachrichtHinzu(text, "nutzer");
  eingabeFeld.value = "";

  chatWartetAufAntwort = true;
  sendenBtn.disabled = true;

  const antwortFeld = fuegeChatNachrichtHinzu("…", "assistent");

  try {
    const response = await fetch(CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nachricht: text, session_id: chatSessionId })
    });

    if (!response.ok) {
      // Das Backend läuft, hat aber einen Fehler gemeldet (z. B. Gemini hat abgelehnt)
      let grund = "";
      try {
        const fehlerDaten = await response.json();
        grund = fehlerDaten.detail || "";
      } catch (e) {
        // Antwort war kein JSON
      }

      if (grund.includes("429") || grund.includes("RESOURCE_EXHAUSTED")) {
        antwortFeld.textContent = "Das Gemini-Kontingent ist gerade aufgebraucht. Bitte warte ein paar Minuten.";
      } else {
        antwortFeld.textContent = "Fehler im Backend (Status " + response.status + "): " + grund;
      }
    } else {
      const daten = await response.json();
      antwortFeld.textContent = daten.antwort;

      // Wurde ein Termin angelegt, die Terminliste und die Monatsansicht neu laden
      if (daten.kalender_geaendert) {
        document.getElementById("calendarButton").click();
      }
    }

  } catch (fehler) {
    // Die Anfrage kam gar nicht beim Backend an
    console.error(fehler);
    antwortFeld.textContent = "Das Backend ist nicht erreichbar. Läuft es auf Port 8000?";
  }

  chatWartetAufAntwort = false;
  sendenBtn.disabled = false;
  verlauf.scrollTop = verlauf.scrollHeight;
  eingabeFeld.focus();
}