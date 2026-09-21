const BACKEND_URL = "http://127.0.0.1:8000";

async function holeWetter() {
  try {
    const standort = await getStandort();

    const response = await fetch(`${BACKEND_URL}/wetter/lesbar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(standort)
    });

    const text = await response.text();
    return text;

  } catch (fehler) {
    console.warn("Browser-Standort fehlgeschlagen, nutze automatischen Fallback:", fehler);

    const response = await fetch(`${BACKEND_URL}/wetter/auto`);
    const text = await response.text();
    return text;
  }
}