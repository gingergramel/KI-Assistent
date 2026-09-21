from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
from pydantic import BaseModel

from weather import get_weather_forecast, format_weather_human, get_weather_auto_human
from news import get_top_news, format_news_human, format_news_html
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