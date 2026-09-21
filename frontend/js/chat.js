function fuegeChatNachrichtHinzu(text, absender) {
  const verlauf = document.getElementById("chat-verlauf");
  const nachricht = document.createElement("div");
  nachricht.classList.add("chat-nachricht", absender);
  nachricht.textContent = text;
  verlauf.appendChild(nachricht);
  verlauf.scrollTop = verlauf.scrollHeight;
}

async function sendeChatNachricht() {
  const eingabeFeld = document.getElementById("chat-eingabe");
  const text = eingabeFeld.value.trim();
  if (!text) return;

  fuegeChatNachrichtHinzu(text, "nutzer");
  eingabeFeld.value = "";

  // Platzhalter, bis der echte Chat-Endpoint im Backend existiert
  fuegeChatNachrichtHinzu("(Antwort folgt, sobald der Chat-Endpoint im Backend steht)", "assistent");
}