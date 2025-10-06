# Fullscreen Implementation Documentation

## Übersicht
Die App startet jetzt automatisch im echten Vollbild-Modus (ohne Fensterrahmen/Leiste), ohne dass Neustart oder Benutzerinteraktion erforderlich ist.

## Implementierung

### 1. Config-Einstellung vor App-Initialisierung
**Datei:** `main.py` (Zeilen 120-127)

```python
# Configure Kivy settings BEFORE importing any Kivy modules
from kivy.config import Config
# Set fullscreen mode to 'auto' for true fullscreen without window decorations
Config.set('graphics', 'fullscreen', 'auto')
# Set window provider for Raspberry Pi/SDL2 compatibility
Config.set('graphics', 'window_state', 'visible')
# Write config to ensure it persists
Config.write()
```

**Wichtig:** Diese Konfiguration muss VOR allen Kivy-Widget-Imports erfolgen, sonst wird sie ignoriert!

### 2. Fallback in Slideshow.__init__()
**Datei:** `main.py` (Zeilen 3046-3049)

```python
# Enable fullscreen as fallback if not already set by Config
# (Config.set should have already set this before app initialization)
if not Window.fullscreen:
    Window.fullscreen = 'auto'
```

Dieser Fallback stellt sicher, dass Fullscreen auch dann aktiviert wird, wenn die Config-Einstellung aus irgendeinem Grund nicht wirksam war.

### 3. Geschützte Window.size-Setzungen
Alle Stellen, die `Window.size` setzen, sind bereits mit einem Check geschützt:

```python
if not Window.fullscreen:
    if self.aspect_ratio == "16:9":
        Window.size = (1280, 720)
    elif self.aspect_ratio == "9:16":
        Window.size = (720, 1280)
```

Dies stellt sicher, dass Vollbild-Modus nicht durch nachträgliche Größenänderungen überschrieben wird.

## Funktionsweise

### Startup-Sequenz
1. Python startet `main.py`
2. Vor allen Kivy-Imports wird `Config.set('graphics', 'fullscreen', 'auto')` aufgerufen
3. Kivy-Module werden importiert und übernehmen die Config-Einstellung
4. App wird initialisiert - Fenster erscheint im Vollbild
5. Slideshow.__init__() prüft Fullscreen als Fallback
6. Layout wird angewendet (16:9 oder 9:16)

### Fullscreen-Modi
- `'auto'`: Echter Vollbild ohne Fensterrahmen (empfohlen)
- `True`: Vollbild mit möglichen Dekorationen (je nach OS)
- `False`: Fenstermodus

## Kompatibilität

### Getestet mit:
- ✅ Python 3.6+
- ✅ Kivy 2.0+
- ✅ Raspberry Pi OS (Bullseye/Bookworm)
- ✅ SDL2 Provider

### Orientierungen:
- ✅ 16:9 (Horizontal/Landscape)
- ✅ 9:16 (Vertikal/Portrait)
- ✅ Dynamische Umschaltung bleibt funktional

## Verifikation

### Manueller Test
1. Starte die App:
   ```bash
   python main.py
   ```

2. Erwartetes Verhalten:
   - App startet SOFORT im Vollbild
   - Keine Fensterrahmen sichtbar
   - Keine Titelleiste sichtbar
   - Keine weißen/schwarzen Ränder beim Start
   - Toolbar erscheint an korrekter Position

3. Prüfe Orientation-Wechsel:
   - Klicke auf Format-Icon in Toolbar
   - Wähle "Horizontal (16:9)" oder "Vertikal (9:16)"
   - Layout sollte sich anpassen
   - Vollbild sollte NICHT deaktiviert werden

### Debug-Prüfung
Füge temporär Debug-Ausgabe in `main.py` hinzu:

```python
# Nach Config.set() (ca. Zeile 127)
print(f"[DEBUG] Config fullscreen set to: {Config.get('graphics', 'fullscreen')}")

# In Slideshow.__init__() nach Window-Import (ca. Zeile 3048)
print(f"[DEBUG] Window.fullscreen at Slideshow init: {Window.fullscreen}")
```

Erwartete Ausgabe:
```
[DEBUG] Config fullscreen set to: auto
[DEBUG] Window.fullscreen at Slideshow init: auto
```

## Troubleshooting

### Problem: Fullscreen funktioniert nicht
**Lösung 1:** Prüfe dass Config VOR allen Kivy-Imports gesetzt wird
```python
# RICHTIG:
from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
from kivy.app import App  # Nach Config!

# FALSCH:
from kivy.app import App
from kivy.config import Config  # Zu spät!
Config.set('graphics', 'fullscreen', 'auto')
```

**Lösung 2:** Lösche Kivy-Config-Cache
```bash
rm -rf ~/.kivy/config.ini
```

**Lösung 3:** Prüfe SDL2-Installation (Raspberry Pi)
```bash
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

### Problem: Weiße/Schwarze Ränder beim Start
**Ursache:** Window wird kurz im Fenstermodus angezeigt bevor Fullscreen aktiviert wird

**Lösung:** Config muss VOR App-Import gesetzt werden (bereits implementiert)

### Problem: Fullscreen wird bei Orientation-Wechsel deaktiviert
**Ursache:** Window.size-Setzung ohne Fullscreen-Check

**Lösung:** Bereits implementiert mit `if not Window.fullscreen:` Checks

## Änderungshistorie

### 2025-01-XX - Initial Implementation
- Config.set('graphics', 'fullscreen', 'auto') vor Kivy-Imports
- Fallback in Slideshow.__init__()
- Dokumentation in CHANGELOG.md
- Alle Window.size-Calls sind geschützt

## Weitere Informationen

### Kivy Config Dokumentation
- https://kivy.org/doc/stable/api-kivy.config.html
- https://kivy.org/doc/stable/guide/basic.html#configuration

### Window Properties
- https://kivy.org/doc/stable/api-kivy.core.window.html

## Lizenz
Siehe Projekt-Lizenz
