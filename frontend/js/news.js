async function holeNews() {
  try {
    const response = await fetch(`${BACKEND_URL}/news/html`);
    const html = await response.text();
    return html;
  } catch (fehler) {
    return "<p>Fehler beim Abrufen der News: " + fehler + "</p>";
  }
}