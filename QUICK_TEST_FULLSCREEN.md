# Schnelltest: Vollbild-Funktionalität

## ⚡ Quick Test Guide (5 Minuten)

### 1. Voraussetzungen prüfen
```bash
# SDL2 installiert? (Raspberry Pi)
dpkg -l | grep libsdl2

# Falls nicht:
sudo apt-get update
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

### 2. App starten
```bash
cd /home/pi/Desktop/v2_Tripple\ S/
python3 main.py
```

### 3. Erwartetes Verhalten ✅

#### ✅ Beim Start:
- [ ] Fenster erscheint SOFORT im Vollbild
- [ ] KEINE Fensterrahmen sichtbar
- [ ] KEINE Titelleiste sichtbar
- [ ] KEINE weißen/schwarzen Ränder
- [ ] Toolbar erscheint an korrekter Position
- [ ] Bilder werden korrekt angezeigt

#### ✅ Orientation-Wechsel:
1. Klicke auf Format-Icon (aspect-ratio) in Toolbar
2. Wähle "Vertikal (9:16)"
   - [ ] Layout wechselt zu vertikal
   - [ ] Toolbar erscheint rechts (vertikal)
   - [ ] Vollbild bleibt AKTIV (keine Rahmen)
3. Wähle "Horizontal (16:9)"
   - [ ] Layout wechselt zu horizontal
   - [ ] Toolbar erscheint unten (horizontal)
   - [ ] Vollbild bleibt AKTIV (keine Rahmen)

### 4. Debug-Modus (Optional)

Temporär in `main.py` nach Zeile 127 einfügen:
```python
print(f"[DEBUG] Config fullscreen: {Config.get('graphics', 'fullscreen')}")
print(f"[DEBUG] Window provider: {Config.get('graphics', 'window_provider')}")
```

Und nach Zeile 3049:
```python
print(f"[DEBUG] Window.fullscreen at init: {Window.fullscreen}")
print(f"[DEBUG] Window.size at init: {Window.size}")
```

Erwartete Ausgabe:
```
[DEBUG] Config fullscreen: auto
[DEBUG] Window provider: sdl2
[DEBUG] Window.fullscreen at init: auto
[DEBUG] Window.size at init: (1920, 1080)  # oder ähnlich
```

### 5. Fehlerbehebung

#### Problem: Fenster nicht im Vollbild
**Prüfe:**
```bash
# 1. Kivy Config löschen (erzwingt Neuinitialisierung)
rm -rf ~/.kivy/config.ini

# 2. App neu starten
python3 main.py
```

**Wenn immer noch nicht funktioniert:**
```python
# In main.py nach Zeile 3049 temporär einfügen:
print(f"Window.fullscreen value: {Window.fullscreen}")
print(f"Window.fullscreen type: {type(Window.fullscreen)}")

# Sollte ausgeben:
# Window.fullscreen value: auto
# Window.fullscreen type: <class 'str'>
```

#### Problem: Schwarzer Bildschirm
**Ursache:** SDL2-Provider Probleme

**Lösung:**
```bash
# Prüfe SDL2-Installation
python3 -c "from kivy.core.window import Window; print(Window.__class__.__module__)"
# Sollte ausgeben: kivy.core.window.window_sdl2

# Falls nicht sdl2:
sudo apt-get install --reinstall libsdl2-dev
```

#### Problem: Fullscreen bei Orientation-Wechsel verloren
**Diagnose:**
```bash
# Prüfe ob Window.size-Setzungen geschützt sind
grep -A2 "Window.size =" main.py | grep -B2 "if not Window.fullscreen"

# Sollte zeigen dass alle Window.size Calls geschützt sind
```

### 6. Erfolgs-Kriterien

✅ **ERFOLG wenn:**
- App startet ohne Fensterrahmen
- Orientation-Wechsel funktioniert
- Vollbild bleibt bei allen Aktionen aktiv
- Keine weißen/schwarzen Ränder

❌ **FEHLER wenn:**
- Fensterrahmen sichtbar beim Start
- Titelleiste erscheint
- Vollbild wird bei Orientation-Wechsel deaktiviert
- Weiße/schwarze Ränder beim Start

### 7. Log-Analyse

```bash
# Projekt-Log prüfen
tail -f ~/Desktop/v2_Tripple\ S/projekt.log | grep -i "window\|fullscreen\|size"

# Nach Startup suchen:
# - Fullscreen-Aktivierung
# - Window-Größen-Änderungen
# - Layout-Anwendung
```

### 8. Schnell-Checkliste

```
PRE-TEST:
[ ] SDL2 installiert
[ ] main.py aktuell (Config vor Imports)
[ ] Kivy Config gelöscht (~/.kivy/config.ini)

STARTUP:
[ ] App startet
[ ] Vollbild aktiv
[ ] Keine Rahmen
[ ] Toolbar sichtbar

ORIENTATION:
[ ] 16:9 → Toolbar unten
[ ] 9:16 → Toolbar rechts
[ ] Vollbild bleibt aktiv

STABILITY:
[ ] 3x App neu starten → immer Vollbild
[ ] 3x Orientation wechseln → immer Vollbild
```

## 📝 Test-Report Template

```markdown
### Fullscreen Test Report

**Datum:** [YYYY-MM-DD]
**Tester:** [Name]
**Hardware:** [z.B. Raspberry Pi 4B]
**OS:** [z.B. Raspberry Pi OS Bookworm]
**Kivy Version:** [z.B. 2.1.0]

#### Startup Test
- Vollbild aktiv: [ ] Ja [ ] Nein
- Keine Rahmen: [ ] Ja [ ] Nein
- Keine Titelleiste: [ ] Ja [ ] Nein
- Screenshots: [Link]

#### Orientation Test
- 16:9 Vollbild: [ ] Ja [ ] Nein
- 9:16 Vollbild: [ ] Ja [ ] Nein
- Wechsel funktioniert: [ ] Ja [ ] Nein

#### Stability Test
- 3x Restart OK: [ ] Ja [ ] Nein
- 3x Orientation OK: [ ] Ja [ ] Nein

#### Probleme
[Beschreibung falls vorhanden]

#### Ergebnis
[ ] ✅ BESTANDEN
[ ] ❌ NICHT BESTANDEN
```

## 🔗 Referenzen

- Technische Details: `FULLSCREEN_IMPLEMENTATION.md`
- Ablauf-Diagramm: `FULLSCREEN_STARTUP_FLOW.md`
- PR-Zusammenfassung: `PR_FULLSCREEN_SUMMARY.md`
- Changelog: `CHANGELOG.md` (Fullscreen-Sektion)

---

**Geschätzte Testzeit:** 5-10 Minuten  
**Schwierigkeit:** Einfach  
**Erforderlich:** Raspberry Pi mit Display/Monitor
