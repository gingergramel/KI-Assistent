(function () {
  const MONATSNAMEN = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
  ];
  const WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];

  const heute = new Date();
  let jahr = heute.getFullYear();
  let monat = heute.getMonth();
  let gewaehlterTag = heute.getDate();
  let termine = [];

  const ansicht = document.getElementById("kalender-ansicht");
  const liste = document.getElementById("calendarOutput");
  const btnMonat = document.getElementById("ansicht-monat");
  const btnListe = document.getElementById("ansicht-liste");

  function uhrzeit(datum) {
    return datum.toLocaleTimeString("de-AT", { hour: "2-digit", minute: "2-digit" });
  }

  // Übernimmt die Termine, die calendar.js vom Backend geladen hat
  function uebernimmTermine() {
    termine = (window.kalenderTermine || []).map((original) => {
      // Ganztägige Termine haben nur ein Datum (JJJJ-MM-TT) ohne Uhrzeit
      if (!original.start.includes("T")) {
        const [j, m, t] = original.start.split("-").map(Number);
        return { original, jahr: j, monat: m - 1, tag: t, zeit: "", zeitText: "ganztägig" };
      }

      const start = new Date(original.start);
      const ende = new Date(original.ende);

      return {
        original,
        jahr: start.getFullYear(),
        monat: start.getMonth(),
        tag: start.getDate(),
        zeit: uhrzeit(start),
        zeitText: uhrzeit(start) + " – " + uhrzeit(ende)
      };
    });
  }

  function termineAm(tag) {
    return termine
      .filter((t) => t.jahr === jahr && t.monat === monat && t.tag === tag)
      .sort((a, b) => a.zeit.localeCompare(b.zeit));
  }

  function wechsleMonat(richtung) {
    monat += richtung;
    if (monat < 0) { monat = 11; jahr--; }
    if (monat > 11) { monat = 0; jahr++; }
    gewaehlterTag = null;
    zeichne();
  }

  function zeichne() {
    ansicht.innerHTML = "";

    // Kopf mit Monatsname und Navigation
    const kopf = document.createElement("div");
    kopf.className = "kal-kopf";

    const titel = document.createElement("div");
    titel.className = "kal-monat-titel";
    titel.textContent = MONATSNAMEN[monat] + " " + jahr;

    const nav = document.createElement("div");
    nav.className = "kal-nav";
    const zurueck = document.createElement("button");
    zurueck.textContent = "‹";
    zurueck.title = "Vorheriger Monat";
    zurueck.addEventListener("click", () => wechsleMonat(-1));
    const heuteBtn = document.createElement("button");
    heuteBtn.textContent = "Heute";
    heuteBtn.addEventListener("click", () => {
      jahr = heute.getFullYear();
      monat = heute.getMonth();
      gewaehlterTag = heute.getDate();
      zeichne();
    });
    const weiter = document.createElement("button");
    weiter.textContent = "›";
    weiter.title = "Nächster Monat";
    weiter.addEventListener("click", () => wechsleMonat(1));
    nav.append(zurueck, heuteBtn, weiter);

    kopf.append(titel, nav);
    ansicht.appendChild(kopf);

    // Raster
    const raster = document.createElement("div");
    raster.className = "kal-raster";

    WOCHENTAGE.forEach((name) => {
      const el = document.createElement("div");
      el.className = "kal-wochentag";
      el.textContent = name;
      raster.appendChild(el);
    });

    const versatz = (new Date(jahr, monat, 1).getDay() + 6) % 7; // Woche beginnt am Montag
    const tageImMonat = new Date(jahr, monat + 1, 0).getDate();

    for (let i = 0; i < versatz; i++) {
      const leer = document.createElement("div");
      leer.className = "kal-tag leer";
      raster.appendChild(leer);
    }

    for (let tag = 1; tag <= tageImMonat; tag++) {
      const zelle = document.createElement("div");
      zelle.className = "kal-tag";

      const istHeute = tag === heute.getDate() && monat === heute.getMonth() && jahr === heute.getFullYear();
      if (istHeute) zelle.classList.add("heute");
      if (tag === gewaehlterTag) zelle.classList.add("gewaehlt");

      const zahl = document.createElement("span");
      zahl.className = "kal-zahl";
      zahl.textContent = tag;
      zelle.appendChild(zahl);

      const anzahl = termineAm(tag).length;
      if (anzahl > 0) {
        const punkte = document.createElement("div");
        punkte.className = "kal-punkte";
        for (let p = 0; p < Math.min(anzahl, 3); p++) {
          const punkt = document.createElement("span");
          punkt.className = "kal-punkt";
          punkte.appendChild(punkt);
        }
        zelle.appendChild(punkte);
      }

      zelle.addEventListener("click", () => {
        gewaehlterTag = tag;
        zeichne();
      });
      raster.appendChild(zelle);
    }

    ansicht.appendChild(raster);

    // Termine des gewählten Tages
    if (gewaehlterTag) {
      const tagesliste = document.createElement("div");
      tagesliste.className = "kal-tagesliste";

      const ueberschrift = document.createElement("div");
      ueberschrift.className = "kal-tages-titel";
      ueberschrift.textContent = gewaehlterTag + ". " + MONATSNAMEN[monat] + " " + jahr;
      tagesliste.appendChild(ueberschrift);

      const heutigeTermine = termineAm(gewaehlterTag);
      if (heutigeTermine.length === 0) {
        const keine = document.createElement("div");
        keine.className = "kal-keine";
        keine.textContent = "Keine Termine an diesem Tag.";
        tagesliste.appendChild(keine);
      } else {
        heutigeTermine.forEach((t) => {
          const eintrag = document.createElement("div");
          eintrag.className = "kal-termin";

          const zeit = document.createElement("span");
          zeit.className = "kal-termin-zeit";
          zeit.textContent = t.zeitText;

          const name = document.createElement("span");
          name.className = "kal-termin-name";
          name.textContent = t.original.titel;

          eintrag.append(zeit, name);

          // Bearbeiten und Löschen, gebaut von calendar.js
          if (window.baueTerminAktionen) {
            eintrag.appendChild(window.baueTerminAktionen(t.original));
          }

          tagesliste.appendChild(eintrag);
        });
      }
      ansicht.appendChild(tagesliste);
    }
  }

  function zeigeAnsicht(art) {
    const monatAktiv = art === "monat";
    ansicht.hidden = !monatAktiv;
    liste.hidden = monatAktiv;
    btnMonat.classList.toggle("aktiv", monatAktiv);
    btnListe.classList.toggle("aktiv", !monatAktiv);
  }

  btnMonat.addEventListener("click", () => zeigeAnsicht("monat"));
  btnListe.addEventListener("click", () => zeigeAnsicht("liste"));

  // Sobald calendar.js neue Termine geladen hat, die Monatsansicht aktualisieren
  document.addEventListener("termine-geladen", () => {
    uebernimmTermine();
    zeichne();
  });

  zeichne();
  zeigeAnsicht("monat");
})();