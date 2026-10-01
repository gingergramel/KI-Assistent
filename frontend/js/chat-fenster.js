(function () {
  const toggle = document.getElementById("chat-toggle");
  const fenster = document.getElementById("chat-section");
  const schliessen = document.getElementById("chat-schliessen");
  const eingabe = document.getElementById("chat-eingabe");

  function oeffnen() {
    fenster.hidden = false;
    toggle.textContent = "✕";
    toggle.title = "Chat schließen";
    eingabe.focus();
  }

  function zuklappen() {
    fenster.hidden = true;
    toggle.textContent = "💬";
    toggle.title = "Chat öffnen";
  }

  toggle.addEventListener("click", () => {
    if (fenster.hidden) {
      oeffnen();
    } else {
      zuklappen();
    }
  });

  schliessen.addEventListener("click", zuklappen);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !fenster.hidden) zuklappen();
  });
})();