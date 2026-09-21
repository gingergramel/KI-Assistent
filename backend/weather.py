import requests
import os
from dotenv import load_dotenv

load_dotenv()


def get_location_by_ip():
    response = requests.get("http://ip-api.com/json/")
    data = response.json()
    return {"lat": data["lat"], "lon": data["lon"], "stadt": data["city"]}



def get_weather_forecast(lat: float, lon: float):
    key = os.getenv("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={key}&units=metric&lang=de"
    response = requests.get(url)
    data = response.json()

    if data.get("cod") != "200":
        fehlermeldung = data.get("message", "Unbekannter Fehler")
        return {"error": fehlermeldung}

    heute = []
    heutiges_datum = data["list"][0]["dt_txt"][:10]

    for eintrag in data["list"]:
        if eintrag["dt_txt"].startswith(heutiges_datum):
            heute.append({
                "uhrzeit": eintrag["dt_txt"][11:16],
                "temperatur": round(eintrag["main"]["temp"], 1),
                "beschreibung": eintrag["weather"][0]["description"],
                "regen_wahrscheinlichkeit": round(eintrag.get("pop", 0) * 100)
            })

    return {"stadt": data["city"]["name"], "datum": heutiges_datum, "verlauf": heute}


def format_weather_human(wetter_daten):
    if "error" in wetter_daten:
        fehler = wetter_daten["error"]
        return "Fehler beim Abrufen der Wetterdaten: " + fehler

    datum = wetter_daten["datum"]
    zeilen = ["Wetterverlauf von " + wetter_daten["stadt"] + " am " + datum + ":"]
    for eintrag in wetter_daten["verlauf"]:
        zeile = "  " + eintrag["uhrzeit"] + " Uhr: " + str(eintrag["temperatur"]) + "C, "
        zeile += eintrag["beschreibung"] + ", Regenwahrscheinlichkeit " + str(eintrag["regen_wahrscheinlichkeit"]) + "%"
        zeilen.append(zeile)
    return "\n".join(zeilen)


def get_weather_auto_human():
    standort = get_location_by_ip()
    daten = get_weather_forecast(standort["lat"], standort["lon"])
    return format_weather_human(daten)