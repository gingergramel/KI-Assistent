from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from calendar_service import get_upcoming_events

from weather import get_weather_forecast, format_weather_human, get_weather_auto_human
from llm import ask_gemini

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


@app.get("/", response_class=PlainTextResponse)
def root():
    """Startseite: zeigt direkt den automatisch erkannten Wetterverlauf als lesbaren Text."""
    return get_weather_auto_human()


@app.get("/wetter/auto", response_class=PlainTextResponse)
def wetter_auto():
    """Standort automatisch per IP erkennen, Wetterverlauf als lesbaren Text zurückgeben."""
    return get_weather_auto_human()


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


@app.get("/llm-test")
def llm_test():
    """Testet, ob die Gemini-API-Verbindung funktioniert."""
    antwort = ask_gemini("Sag mir in einem Satz, dass die Verbindung funktioniert.")
    return {"antwort": antwort}

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