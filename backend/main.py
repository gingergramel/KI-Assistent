from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
from pydantic import BaseModel

from calendar_service import get_upcoming_events, create_event, check_calendar_availability
from mail_service import get_inbox_mails
from weather import get_weather_forecast, format_weather_human, get_weather_auto_human, get_weather_auto_json
from news import get_top_news, format_news_human, format_news_html
from llm import ask_gemini, chat_mit_gemini

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # für Entwicklung offen, später auf konkrete Domain einschränken
    allow_methods=["*"],
    allow_headers=["*"],
)


class Koordinaten(BaseModel):
    lat: float
    lon: float


class NeuerTermin(BaseModel):
    titel: str
    start: str  # Format: "2026-10-05T14:30"
    dauer_minuten: int = 60


class TerminPruefung(BaseModel):
    start: datetime
    dauer_minuten: int = 60


class ChatAnfrage(BaseModel):
    nachricht: str
    session_id: str = "standard"


@app.get("/", response_class=PlainTextResponse)
def root():
    """Startseite: zeigt direkt den automatisch erkannten Wetterverlauf als lesbaren Text."""
    return get_weather_auto_human()


@app.get("/wetter/auto", response_class=PlainTextResponse)
def wetter_auto():
    """Standort automatisch per IP erkennen, Wetterverlauf als lesbaren Text zurückgeben."""
    return get_weather_auto_human()


@app.get("/wetter/auto/json")
def wetter_auto_json():
    """Standort automatisch erkennen, Wetterdaten strukturiert zurückgeben (für Kartenanzeige)."""
    return get_weather_auto_json()


@app.post("/wetter")
def wetter(koordinaten: Koordinaten):
    """Wetterverlauf für gegebene Koordinaten, strukturiert (für die KI/Weiterverarbeitung)."""
    daten = get_weather_forecast(koordinaten.lat, koordinaten.lon)
    return daten


@app.post("/wetter/lesbar", response_class=PlainTextResponse)
def wetter_lesbar(koordinaten: Koordinaten):
    """Wetterverlauf für gegebene Koordinaten, als lesbarer Text."""
    daten = get_weather_forecast(koordinaten.lat, koordinaten.lon)
    return format_weather_human(daten)


@app.get("/news")
def news():
    """News-Artikel, strukturiert (für die KI/Weiterverarbeitung)."""
    return get_top_news()


@app.get("/news/lesbar", response_class=PlainTextResponse)
def news_lesbar():
    """News-Artikel als lesbarer Text."""
    daten = get_top_news()
    return format_news_human(daten)


@app.get("/news/html", response_class=HTMLResponse)
def news_html():
    """News-Artikel als HTML mit klickbaren Links."""
    daten = get_top_news()
    return format_news_html(daten)


@app.get("/llm-test")
def llm_test():
    """Testet, ob die Gemini-API-Verbindung funktioniert."""
    antwort = ask_gemini("Sag mir in einem Satz, dass die Verbindung funktioniert.")
    return {"antwort": antwort}


@app.post("/chat")
def chat(anfrage: ChatAnfrage):
    """Nimmt eine Nutzernachricht entgegen. Gemini beantwortet sie und ruft bei Bedarf Kalender, Wetter und News auf."""
    if not anfrage.nachricht.strip():
        raise HTTPException(status_code=400, detail="Die Nachricht darf nicht leer sein.")

    try:
        return chat_mit_gemini(anfrage.session_id, anfrage.nachricht)
    except Exception as fehler:
        print("Chat-Fehler:", fehler)
        raise HTTPException(status_code=502, detail="Gemini hat nicht geantwortet: " + str(fehler))


@app.get("/kalender")
def kalender():
    """Liest die nächsten Termine aus dem Google-Kalender."""
    events = get_upcoming_events()

    termine = []

    for event in events:
        start = event["start"].get(
            "dateTime",
            event["start"].get("date")
        )

        termine.append({
            "titel": event.get("summary", "Ohne Titel"),
            "start": start
        })

    return {"termine": termine}


@app.post("/kalender/termin")
def termin_anlegen(termin: NeuerTermin):
    """Prüft die Verfügbarkeit und erstellt den Termin."""

    start_datetime = datetime.fromisoformat(termin.start)

    ergebnis = create_event(
        termin.titel,
        start_datetime,
        termin.dauer_minuten
    )

    if not ergebnis["erstellt"]:
        return {
            "erstellt": False,
            "nachricht": ergebnis["nachricht"],
            "konflikte": ergebnis.get("konflikte", [])
        }

    erstelltes_event = ergebnis["termin"]

    return {
        "erstellt": True,
        "nachricht": "Termin wurde erfolgreich erstellt.",
        "titel": erstelltes_event.get("summary"),
        "start": erstelltes_event["start"].get("dateTime"),
        "ende": erstelltes_event["end"].get("dateTime")
    }


@app.post("/kalender/pruefen")
def kalender_pruefen(termin: TerminPruefung):
    """Prüft, ob ein Zeitraum im Kalender frei ist."""
    return check_calendar_availability(
        termin.start,
        termin.dauer_minuten
    )


@app.get("/api/mails")
def get_mails():
    return get_inbox_mails(20)
#todo wenn man mehr mails will, dann muss man die variable eine zeile darüber ändern.