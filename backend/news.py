import requests
import os
from dotenv import load_dotenv

load_dotenv()


def get_top_news(suchbegriff="Österreich", anzahl=5):
    """Holt aktuelle Nachrichtenartikel zu einem Suchbegriff."""
    key = os.getenv("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/everything?q={suchbegriff}&language=de&sortBy=publishedAt&pageSize={anzahl}&apiKey={key}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") != "ok":
        return {"error": data.get("message", "Unbekannter Fehler")}

    artikel = []
    for eintrag in data["articles"]:
        artikel.append({
            "titel": eintrag["title"],
            "quelle": eintrag["source"]["name"],
            "url": eintrag["url"]
        })

    return {"artikel": artikel}


def format_news_human(news_daten):
    """Formatiert News zu lesbarem Text (ohne Links)."""
    if "error" in news_daten:
        return "Fehler beim Abrufen der News: " + news_daten["error"]

    zeilen = ["Aktuelle Schlagzeilen:"]
    for i, eintrag in enumerate(news_daten["artikel"], start=1):
        zeile = str(i) + ". " + eintrag["titel"] + " (" + eintrag["quelle"] + ")"
        zeilen.append(zeile)
    return "\n".join(zeilen)


def format_news_html(news_daten):
    """Formatiert News als HTML mit klickbaren Links."""
    if "error" in news_daten:
        return "<p>Fehler beim Abrufen der News: " + news_daten["error"] + "</p>"

    zeilen = []
    for i, eintrag in enumerate(news_daten["artikel"], start=1):
        zeile = f'<p>{i}. <a href="{eintrag["url"]}" target="_blank">{eintrag["titel"]}</a> ({eintrag["quelle"]})</p>'
        zeilen.append(zeile)
    return "".join(zeilen)