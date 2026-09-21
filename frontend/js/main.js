document.addEventListener("DOMContentLoaded", () => {
  const briefingBtn = document.getElementById("briefing-btn");
  const wetterAusgabe = document.getElementById("wetter-ausgabe");

  briefingBtn.addEventListener("click", async () => {
    wetterAusgabe.textContent = "Lade Wetterdaten...";
    const text = await holeWetter();
    wetterAusgabe.textContent = text;
  });

  const newsBtn = document.getElementById("news-btn");
  const newsAusgabe = document.getElementById("news-ausgabe");

  newsBtn.addEventListener("click", async () => {
    newsAusgabe.innerHTML = "Lade News...";
    const html = await holeNews();
    newsAusgabe.innerHTML = html;
  });

  const chatSendenBtn = document.getElementById("chat-senden-btn");
  const chatEingabe = document.getElementById("chat-eingabe");

  chatSendenBtn.addEventListener("click", sendeChatNachricht);
  chatEingabe.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendeChatNachricht();
  });
});