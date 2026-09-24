const BACKEND_URL = "http://127.0.0.1:8000";

function bestimmeWetterKlasse(beschreibung) {
  const text = beschreibung.toLowerCase();
  if (text.includes("gewitter")) return "karte-gewitter";
  if (text.includes("regen") || text.includes("schauer")) return "karte-regen";
  if (text.includes("schnee")) return "karte-schnee";
  if (text.includes("klar") || text.includes("sonnig")) return "karte-sonnig";
  if (text.includes("bewölkt") || text.includes("wolken") || text.includes("bedeckt")) return "karte-bewoelkt";
  return "karte-standard";
}

function baueWetterKarten(daten) {
  if (daten.error) {
    return `<p>Fehler beim Abrufen der Wetterdaten: ${daten.error}</p>`;
  }

  let html = `<h3 class="wetter-titel">${daten.stadt} – ${daten.datum}</h3>`;
  html += `<div class="wetter-karten">`;

  daten.verlauf.forEach(eintrag => {
    const klasse = bestimmeWetterKlasse(eintrag.beschreibung);
    html += `
      <div class="wetter-karte ${klasse}">
        <div class="wetter-uhrzeit">${eintrag.uhrzeit} Uhr</div>
        <div class="wetter-temp">${eintrag.temperatur}°C</div>
        <div class="wetter-beschreibung">${eintrag.beschreibung}</div>
        <div class="wetter-regen">🌧️ ${eintrag.regen_wahrscheinlichkeit}%</div>
      </div>
    `;
  });

  html += `</div>`;
  return html;
}

async function holeWetter() {
  try {
    const standort = await getStandort();
    const response = await fetch(`${BACKEND_URL}/wetter`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(standort)
    });
    const daten = await response.json();
    return baueWetterKarten(daten);
  } catch (fehler) {
    console.warn("Browser-Standort fehlgeschlagen, nutze automatischen Fallback:", fehler);
    const response = await fetch(`${BACKEND_URL}/wetter/auto/json`);
    const daten = await response.json();
    return baueWetterKarten(daten);
  }
}