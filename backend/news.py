import html
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()


def get_top_news(suchbegriff="Österreich", anzahl=5):
    """Holt aktuelle Nachrichtenartikel zu einem Suchbegriff."""
    key = os.getenv("NEWS_API_KEY")
    response = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": suchbegriff,
            "language": "de",
            "sortBy": "publishedAt",
            "pageSize": anzahl + 5,  # Reserve, falls Artikel aussortiert werden
            "apiKey": key,
        },
    )
    data = response.json()

    if data.get("status") != "ok":
        return {"error": data.get("message", "Unbekannter Fehler")}

    artikel = []
    for eintrag in data["articles"]:
        if not eintrag.get("title") or eintrag["title"] == "[Removed]":
            continue
        artikel.append({
            "titel": eintrag["title"],
            "quelle": eintrag["source"]["name"],
            "url": eintrag["url"],
            "beschreibung": eintrag.get("description") or "",
            "datum": eintrag.get("publishedAt") or "",
        })

    return {"artikel": artikel[:anzahl]}


def formatiere_datum(iso_text):
    """Wandelt '2026-09-24T12:30:00Z' in '24.09.2026, 14:30' um."""
    if not iso_text:
        return ""
    try:
        zeit = datetime.fromisoformat(iso_text.replace("Z", "+00:00")).astimezone()
        return zeit.strftime("%d.%m.%Y, %H:%M")
    except ValueError:
        return ""


def format_news_human(news_daten):
    """Formatiert News zu lesbarem Text (ohne Links)."""
    if "error" in news_daten:
        return "Fehler beim Abrufen der News: " + news_daten["error"]

    zeilen = ["Aktuelle Schlagzeilen:"]
    for i, eintrag in enumerate(news_daten["artikel"], start=1):
        zeilen.append(str(i) + ". " + eintrag["titel"] + " (" + eintrag["quelle"] + ")")
    return "\n".join(zeilen)


def format_news_html(news_daten):
    """Formatiert News als klickbare Karten (ohne Bilder)."""
    if "error" in news_daten:
        return '<p class="news-fehler">Fehler beim Abrufen der News: ' + html.escape(news_daten["error"]) + "</p>"

    karten = []
    for eintrag in news_daten["artikel"]:
        titel = html.escape(eintrag["titel"])
        quelle = html.escape(eintrag["quelle"])
        url = html.escape(eintrag["url"], quote=True)
        beschreibung = html.escape(eintrag["beschreibung"])
        datum = formatiere_datum(eintrag["datum"])

        karten.append(
            f'<a class="news-karte" href="{url}" target="_blank" rel="noopener">'
            f'<div class="news-text">'
            f'<div class="news-quelle">{quelle}</div>'
            f'<div class="news-titel">{titel}</div>'
            f'<div class="news-beschreibung">{beschreibung}</div>'
            f'<div class="news-datum">{datum}</div>'
            f'</div>'
            f'</a>'
        )
    return "".join(karten)