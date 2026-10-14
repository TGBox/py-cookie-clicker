# py-cookie-clicker: Cosmic Asteroid Miner 🚀

Ein moderner Sci-Fi Space-Mining Clicker für den Desktop, entwickelt mit **Python 3.11+** und **PySide6**.

Baue im Weltraum wertvollen **Sternenstaub** ab, errichte Flotten von Bergbau-Drohnen, orbitale Raffinerien und gigantische Dyson-Schwärme, fange goldene Kometen und schalte mächtige Technologien frei!

---

## Features

- **Interaktiver Asteroid & Feedback**:
  - Dynamischer Klick-Squeeze-Effekt, schwebende Erzzahlen (`+X`), funkelnde Sternenstaub-Partikel.
  - 5 % Chance auf kritische Treffer mit 10-facher Ausbeute.
- **Flotte & Gebäude-Shop**:
  - Exponentiell skalierender Shop für Bergbau-Einheiten (Mining-Drohne, Plasma-Bohrer, Schwerer Rover, Tiefbohr-Plattform, Orbitale Station, Raffinerie-Schiff, Dyson-Schwarm, Antimaterie-Ernter).
  - Mengenauswahl: `1x`, `10x`, `100x` oder `MAX` für schnellen Ausbau.
- **Forschung & Upgrades**:
  - Verdopple Klickkraft und Drohneneffizienz oder steigere die galaktische Gesamtproduktion.
- **Zufallsereignisse (Goldene Kometen)**:
  - Vorbeifliegende goldene Kometen bescheren massive Bonus-Ressourcen oder lösen eine **Hyper-Frenzy** (7x Produktion) aus!
- **Soundeffekte & Audio**:
  - Integrierte prozedural synthetisierte Retro-Soundeffekte (Laserzaps, Kometen-Glocken, Kauf-Jingles) mit Stummschalt-Option.
- **Errungenschaften & Statistik**:
  - 8 freischaltbare Trophäen für Klicks, Gesamtausbeute und Flottengröße.
- **Persistenz & Optionen**:
  - Automatisches Speichern alle 30 Sekunden sowie beim Schließen.
  - Manueller Save, Spielstand-Reset mit Sicherheitsabfrage und Base64-Export/Import zum Teilen oder Sichern.
- **Fenstermodi**:
  - Vollbild-Umschaltung per **F11** oder HUD-Button, Fenstergröße und -position werden in `QSettings` persistent gespeichert.

---

## Voraussetzungen

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

---

## Setup & Ausführung

```bash
# Abhängigkeiten synchronisieren
uv sync

# Spiel starten
uv run main
# oder:
uv run py-cookie-clicker

# Test-Suite ausführen
uv run test

# Code formatieren und prüfen
uv run format
uv run lint

# Standalone-Exe bauen
uv run build
```

---

## Projektstruktur

```text
py-cookie-clicker/
├── src/
│   ├── assets/              # PNG/JPG Spielgrafiken & generierte Sound-WAVs
│   ├── widgets/
│   │   ├── asteroid_widget.py   # Asteroiden-Canvas, Partikel & Kometen
│   │   ├── hud_widget.py        # Obere Statusleiste & Währungsanzeige
│   │   ├── shop_widget.py       # Flotten-Shop & Upgrade-Regal
│   │   └── settings_dialog.py   # Errungenschaften, Statistik & Save-Import/Export
│   ├── audio.py             # Synthetisierte Soundeffekte & Audiomanager
│   ├── game_engine.py       # Simulations-Tick, Kometen & Buffs
│   ├── models.py            # Wirtschaftsformeln, Gebäude, Upgrades & State
│   ├── save_manager.py      # Atomares JSON-Speichern & Base64 Export/Import
│   ├── utils.py             # Deutsche Zahlenformatierung (Mio., Mrd.)
│   ├── build.py             # PyInstaller Build-Script
│   └── main.py              # Anwendungs-Einstiegspunkt & QSS Stylesheet
├── tests/                   # Umfassende Pytest Test-Suite (22 Tests)
├── pyproject.toml
└── README.md
```
