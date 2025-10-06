# Fullscreen Startup Flow

## Visueller Ablauf: App-Start im Vollbild-Modus

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Python startet main.py                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Standard Python Imports (os, json, hashlib, etc.)           │
│    ├── logging setup                                            │
│    └── debug_logger initialisiert                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ⭐ KRITISCH: Kivy Config VOR Widget-Imports                  │
│    ┌────────────────────────────────────────────────────────┐  │
│    │ from kivy.config import Config                         │  │
│    │ Config.set('graphics', 'fullscreen', 'auto')           │  │
│    │ Config.set('graphics', 'window_state', 'visible')      │  │
│    │ Config.write()                                         │  │
│    └────────────────────────────────────────────────────────┘  │
│                                                                  │
│    ❗ Muss VOR kivy.app, kivy.uix.* etc. erfolgen!             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Kivy Widget Imports (übernehmen Config)                     │
│    ├── from kivy.app import App                                │
│    ├── from kivy.uix.floatlayout import FloatLayout            │
│    ├── from kivy.core.window import Window ← Config angewendet │
│    └── ... weitere Kivy-Importe                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Konstanten & Konfiguration (KONFIG-Sektion)                 │
│    ├── APP_DIR, IMAGE_DIR, IMPORT_DIR                          │
│    ├── DEFAULT_INTERVAL, FADE_DUR, etc.                        │
│    └── EFFECTS_AVAILABLE                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Helper-Funktionen & Klassen                                  │
│    ├── hash_password()                                          │
│    ├── load_accounts()                                          │
│    ├── ModeManager                                              │
│    └── ... weitere Klassen                                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Slideshow-Klasse Initialisierung                            │
│    │                                                             │
│    ├── def __init__(self, mode_manager, **kw):                 │
│    │   ├── Load persisted settings (aspect_ratio, etc.)        │
│    │   │                                                        │
│    │   ├── 🔍 Check & Fallback:                                │
│    │   │   ┌────────────────────────────────────────────────┐ │
│    │   │   │ if not Window.fullscreen:                      │ │
│    │   │   │     Window.fullscreen = 'auto'  # Fallback     │ │
│    │   │   └────────────────────────────────────────────────┘ │
│    │   │   (Normalerweise bereits gesetzt durch Config!)      │
│    │   │                                                        │
│    │   ├── Setup screen dimensions                             │
│    │   ├── Create image widgets                                │
│    │   └── Schedule _setup_window_size() callback              │
│    │                                                             │
│    └── Callback: _setup_window_size()                          │
│        ├── Get actual screen dimensions                        │
│        ├── ⚠️ Check: if not Window.fullscreen:                │
│        │   └── Window.size = (1280, 720) or (720, 1280)       │
│        │       (Nur wenn NICHT Fullscreen!)                    │
│        └── Apply layout (_apply_layout())                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. if __name__ == "__main__":                                  │
│    ├── Start upload_server (background thread)                 │
│    ├── app = KioskMDApp()                                      │
│    ├── Window.bind(on_mouse_down=...)                          │
│    └── app.run() ← App startet im VOLLBILD ✨                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   🖥️  VOLLBILD-FENSTER         │
            │                                │
            │   ┌─────────────────────────┐ │
            │   │                         │ │
            │   │    Slideshow läuft      │ │
            │   │    ohne Rahmen/Leiste   │ │
            │   │                         │ │
            │   └─────────────────────────┘ │
            └───────────────────────────────┘
```

## Wichtige Checkpoints

### ✅ Checkpoint 1: Config-Reihenfolge
```python
# ✅ RICHTIG:
from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
from kivy.app import App  # NACH Config!

# ❌ FALSCH:
from kivy.app import App  # VOR Config - zu spät!
from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
```

### ✅ Checkpoint 2: Fallback-Logik
```python
# In Slideshow.__init__():
if not Window.fullscreen:  # Prüft ob Config wirksam war
    Window.fullscreen = 'auto'  # Fallback falls nicht
```

### ✅ Checkpoint 3: Window.size Schutz
```python
# In _setup_window_size() & _select_format():
if not Window.fullscreen:  # NUR im Fenstermodus
    Window.size = (1280, 720)  # Größe anpassen
# Im Fullscreen-Modus wird Window.size NICHT gesetzt
```

## Mögliche Fehlerquellen

### ❌ Problem 1: Config zu spät gesetzt
```
Symptom: App startet im Fenstermodus
Ursache: Config.set() nach Kivy-Widget-Imports
Lösung: Config VOR allen kivy.uix.* Imports
```

### ❌ Problem 2: Config wird überschrieben
```
Symptom: Fullscreen kurz aktiv, dann Fenstermodus
Ursache: Window.size ohne Fullscreen-Check
Lösung: Bereits implementiert mit if not Window.fullscreen
```

### ❌ Problem 3: SDL2 nicht verfügbar
```
Symptom: App startet nicht / schwarzer Bildschirm
Ursache: SDL2-Bibliotheken fehlen (Raspberry Pi)
Lösung: sudo apt-get install libsdl2-*
```

## Verification-Sequenz

### Test 1: Startup
```bash
python main.py
# Erwartung:
# - Fenster erscheint SOFORT im Vollbild
# - Keine Rahmen/Leiste sichtbar
# - Keine kurze Fensteranzeige vor Fullscreen
```

### Test 2: Orientation-Wechsel
```
1. App läuft im Vollbild (16:9)
2. Klick auf Format-Icon
3. Wähle "Vertikal (9:16)"
# Erwartung:
# - Layout wechselt zu 9:16
# - Fullscreen bleibt aktiv
# - Keine Größenänderung des Fensters
```

### Test 3: Debug-Ausgabe
```python
# Temporär hinzufügen für Test:
print(f"[1] Config fullscreen: {Config.get('graphics', 'fullscreen')}")
print(f"[2] Window.fullscreen: {Window.fullscreen}")

# Erwartete Ausgabe:
# [1] Config fullscreen: auto
# [2] Window.fullscreen: auto
```

## Referenzen

### Kivy Config Order
- Config muss vor Widget-Imports gesetzt werden
- https://kivy.org/doc/stable/api-kivy.config.html

### Fullscreen Modi
- `'auto'`: Echter Vollbild ohne Dekorationen (empfohlen)
- `True`: Vollbild mit möglichen Dekorationen
- `False`: Fenstermodus

### SDL2 Provider (Raspberry Pi)
- Standard-Provider für Raspberry Pi OS
- Unterstützt echten Vollbild-Modus
- Erfordert libsdl2-* Pakete
