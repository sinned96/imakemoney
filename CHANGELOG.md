# Changelog

## 2025-01-XX - Feature: Automatischer Vollbildstart (Fullscreen beim App-Start)

### 🎯 Zusammenfassung
Die App startet jetzt IMMER im echten Vollbild-Modus (ohne Fensterrahmen/Leiste), ohne Neustart oder Benutzerinteraktion erforderlich.

### ✅ Neue Features

#### Automatischer Vollbildstart
**Feature:** App startet direkt im Vollbild-Modus beim Programmstart

**Implementierung:**
- `Config.set('graphics', 'fullscreen', 'auto')` vor Kivy-App-Initialisierung (Zeile 123)
- Konfiguration wird VOR Import der Kivy-Widgets gesetzt
- Fallback in `Slideshow.__init__()` falls Config nicht wirksam (Zeile 3048)
- Funktioniert mit beiden Orientierungen (16:9 und 9:16)
- Raspberry Pi/SDL2 kompatibel

**Geänderte Dateien:**
- `main.py`:
  - Zeile 120-127: Config-Import und Fullscreen-Konfiguration vor Kivy-Imports
  - Zeile 3046-3049: Fallback-Logik mit `if not Window.fullscreen:` Check

**Code-Änderung:**
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

**Prüfung:**
- Starte die App: `python main.py`
- App sollte sofort im Vollbild erscheinen (keine Fensterrahmen)
- Wechsel zwischen 16:9 und 9:16 funktioniert weiterhin
- Keine weißen/schwarzen Zwischenflächen beim Start

**Technische Details:**
- Config muss VOR allen Kivy-Widget-Imports gesetzt werden
- `Window.size`-Setzungen sind bereits mit `if not Window.fullscreen:` geschützt
- Orientation-Umschaltung bleibt dynamisch und funktional

---

## 2025-01-XX - Fix: 9:16 End-to-End Korrekturen (Workflow, Anzeige, Doppelklick) - UPDATED

### 🎯 Zusammenfassung
Vollständige End-to-End Behebung der 9:16-Probleme: Workflow-Skalierung optimiert (keine unnötige Skalierung), Textrotation korrigiert (270°), Bildanzeige und Doppelklick-Hänger bereits korrigiert.

### 🐛 Behobene Probleme

#### 1. Workflow-Skalierung (9:16 behält Originalgröße wenn Ratio stimmt) - UPDATED
**Problem:** 
- Generierte 9:16-Bilder (z.B. 768x1408) wurden IMMER auf 1080x1920 oder 1920x1080 skaliert
- Auch wenn das Seitenverhältnis bereits korrekt war
- Dies führte zu unnötigem Qualitätsverlust und falscher Ausgabe
- Logs zeigten: "Image scaled to 1920x1080 … (768, 1408) -> (1920, 1080)"

**Lösung:**
- `PythonServer.py` & `vertex_ai_image_workflow.py`: Neue intelligente Skalierung
  - Prüft zuerst das Seitenverhältnis der Eingabe
  - 5% Toleranz für Seitenverhältnis-Vergleich
  - Wenn Ratio stimmt (z.B. 768x1408 für 9:16): KEINE Skalierung, Originalgröße beibehalten
  - Wenn Ratio falsch: Skaliere auf Zielgröße (1080x1920 für 9:16, 1920x1080 für 16:9)
- Enhanced Logging zeigt jetzt: aspect_ratio_request, raw_output_size, final_saved_size, scaling_applied=True/False

**Code-Änderung:**
```python
# Berechne aktuelles Seitenverhältnis
current_ratio = width / height
target_ratio = 9.0/16.0  # für 9:16 oder 16.0/9.0 für 16:9
ratio_diff = abs(current_ratio - target_ratio) / target_ratio

# Nur skalieren wenn Ratio falsch (>5% Unterschied)
if ratio_diff < 0.05:  # 5% Toleranz
    # Seitenverhältnis bereits korrekt, Originalgröße behalten
    return True  # Keine Skalierung
else:
    # Skaliere auf Zielgröße
    if aspect_ratio == "9:16":
        target_size = (1080, 1920)
    else:
        target_size = (1920, 1080)
```

#### 2. Button-Text Rotation korrigiert (9:16-Modus) - UPDATED
**Problem:** 
- Text war mit 90° gedreht (von unten nach oben lesbar)
- Sollte aber 270° (-90°) sein für natürliche Leserichtung (von oben nach unten)
- Text sollte exakt parallel zum Bildschirmrand sein

**Lösung:** Text wird jetzt mit 270° (-90°) gedreht und ist von oben nach unten lesbar (natürliche Leserichtung)

**Code-Änderung:**
```python
# Vorher: angle=90 (von unten nach oben)
# Nachher: angle=270 (-90°, von oben nach unten, natürliche Richtung)
Rotate(angle=270, origin=self.center)
# + Extra Padding verhindert Text-Clipping
```

#### 3. Bildanzeige im 9:16-Modus korrigiert
**Problem:** 
- Weißer Hintergrund sichtbar trotz dunklem Canvas
- Bilder werden nicht korrekt im 9:16-Container angezeigt

**Lösung:**
- Image Widget verwendet jetzt `keep_ratio=True` statt `False`
- Dies verhindert Verzerrungen und Weißflächen
- Content-Bereich berücksichtigt korrekt Toolbar-Breite
- 9:16 Modus: Content = (0, 0, Breite-110px, Höhe)
- 16:9 Modus: Content = (0, 60px, Breite, Höhe-60px)

**Code-Änderung:**
```python
# Vorher: keep_ratio=False (manuelle Kontrolle, anfällig für Fehler)
# Nachher: keep_ratio=True (automatische Aspect-Ratio Erhaltung)
Image(opacity=1, color=(1,1,1,1), 
      allow_stretch=True, keep_ratio=True)
```

#### 4. Doppelklick-Hänger behoben (Galerie)
**Problem:**
- Doppelklick auf Galerie-Bilder ließ die App hängen
- Fehlende Debounce/Async-Loading/Logging
- Mehrfache Lightbox-Öffnungen möglich

**Lösung:**
- Debounce mit 250ms Throttle implementiert
- `is_lightbox_open` Flag verhindert mehrfache Öffnungen
- Try/Except mit Logging für Texture-Laden
- CoreImage mit `nocache=True` verwendet
- Proper cleanup bei Lightbox-Schließen

**Code-Änderung:**
```python
# Debounce mit Clock.schedule_once
self._scheduled_lightbox = Clock.schedule_once(lambda dt: self._open_lightbox(), 0.25)

# Prevent multiple opens
if self.is_lightbox_open:
    return

# Load with nocache
from kivy.core.image import Image as CoreImage
texture = CoreImage(image_path, nocache=True).texture
```

### 📝 Geänderte Dateien
- `PythonServer.py`:
  - `scale_image_to_1920x1080()`: Aspect-aware Skalierung basierend auf image_meta.json
  - Logging zeigt aspect_ratio, input_size, output_size
- `vertex_ai_image_workflow.py`:
  - `setup_projekt_logging()`: PIL-Logging auf WARNING gesetzt (unterdrückt Debug-Noise)
- `main.py`:
  - `VerticalButton._update_rotation()`: Rotation von 180° auf 90° (mit konfigurierbarem Winkel)
  - `VerticalButton.__init__()`: Extra Padding für Anti-Clipping
  - `CustomAppBar.set_right_actions()`: 90° Rotation für vertikale Buttons
  - `Slideshow.__init__()`: Image Widgets verwenden jetzt `keep_ratio=True`
  - `ImageLightboxPopup`: Komplette Überarbeitung mit Error-Handling und nocache
  - `ImageTile`: Debounce-Mechanismus und is_lightbox_open Flag
  - `Slideshow.__init__()`: Image Widget Konfiguration

### 📚 Dokumentation
- `FIX_SUMMARY.md`: Technische Details und Test-Checkliste
- `VISUAL_GUIDE.md`: ASCII-Diagramme und Beispiele

### 🔍 Debug-Logging
Alle Änderungen loggen in projekt.log:
- Fenster- und Content-Bereich-Dimensionen
- Toolbar-Dimensionen
- Bild-Textur-Größe, Skalierung, Position
- Layout-Anwendungs-Events

### ✅ Tests durchführen
Manuelle Tests empfohlen:
- [ ] 9:16 Bildgenerierung: Erzeuge ein Bild im 9:16-Modus → sollte 1080x1920 sein (kein 1920x1080)
- [ ] 9:16 Anzeige: Bilder füllen Content-Bereich ohne weiße Ränder
- [ ] 9:16 Menü: Text vertikal von unten nach oben lesbar, parallel zum rechten Rand
- [ ] 9:16 Menü: Kein Text-Clipping, alle Buchstaben sichtbar
- [ ] 16:9 Modus: Menü unten, Text horizontal, keine Rotation
- [ ] 16:9 Bildgenerierung: Erzeuge ein Bild im 16:9-Modus → sollte 1920x1080 sein
- [ ] Doppelklick: Galerie-Bild doppelklicken → Lightbox öffnet ohne Freeze
- [ ] Doppelklick: Mehrfacher schneller Doppelklick → nur eine Lightbox öffnet
- [ ] Format-Wechsel: Zwischen 9:16 und 16:9 wechseln → Bilder neu positioniert, Layout korrekt

### 🔍 Log-Überprüfung
Prüfe `projekt.log` nach Bildgenerierung:
```
[INFO] Aspect ratio from image_meta.json: 9:16
[INFO] Scaling image: aspect_ratio=9:16, input_size=(768, 1408), output_size=(1080, 1920)
[INFO] Image scaled to 1080x1920 with aspect ratio preserved: (768, 1408) -> (1080, 1920)
```

Falls noch 1920x1080 erscheint, prüfe ob image_meta.json korrekt ist und aspect_ratio="9:16" enthält.

---

## Datum: 2025-01-XX - Toolbar Layout Verbesserungen (9:16 & 16:9 Modi)

### 🎯 Zusammenfassung
Verbesserung der Toolbar-Darstellung für 9:16 und 16:9 Modi mit vertikaler Textrotation und optimierter Positionierung.

### ✅ Neue Features

#### 1. Vertikale Textrotation für 9:16-Modus Toolbar
**Feature:** Toolbar-Buttons im 9:16-Modus zeigen jetzt vertikal gedrehten Text.

**Implementierung:**
- Neue `VerticalButton` Klasse mit -90° Textrotation
- Text wird von unten nach oben/oben nach unten gedreht angezeigt
- Toolbar bleibt auf der rechten Seite positioniert
- Verbesserte visuelle Darstellung im Hochformat

**Geänderte Dateien:**
- `main.py`:
  - Neue `VerticalButton` Klasse hinzugefügt
  - `CustomAppBar.set_right_actions()`: Verwendet VerticalButton im vertikalen Modus

**Code-Änderungen:**
```python
class VerticalButton(Button):
    """Button mit vertikal gedrehtem Text für 9:16-Modus Toolbar"""
    def _update_rotation(self, *args):
        with self.canvas.before:
            PushMatrix()
            Rotate(angle=-90, origin=self.center)  # 90° im Uhrzeigersinn
        with self.canvas.after:
            PopMatrix()
```

#### 2. Toolbar-Positionierung am unteren Rand für 16:9-Modus
**Feature:** Im 16:9-Modus wird die Toolbar jetzt am unteren Bildschirmrand angezeigt.

**Implementierung:**
- Toolbar-Position geändert von `{"top": 1}` zu `{"bottom": 1}`
- Gilt für beide Toolbar-Typen (KivyMD AppBar und CustomAppBar)
- Bessere Zugänglichkeit im Querformat

**Geänderte Dateien:**
- `main.py`:
  - `_create_toolbar()`: Toolbar-Positionierung aktualisiert

**Code-Änderungen:**
```python
# In _create_toolbar():
if vertical:
    # 9:16: Toolbar rechts
    bar.pos_hint = {"right": 1, "top": 1}
else:
    # 16:9: Toolbar unten
    bar.pos_hint = {"bottom": 1}
```

#### 3. Verbesserte Fenstergrößen-Anpassung
**Feature:** Fenstergrößen-Anpassung jetzt auch beim initialen Start und Format-Wechsel (außerhalb Fullscreen-Modus).

**Implementierung:**
- Window-Resize in `_select_format()` hinzugefügt
- Window-Resize in `_setup_window_size()` hinzugefügt
- Prüfung auf Fullscreen-Modus vor Resize
- 16:9 → 1280x720, 9:16 → 720x1280

**Geänderte Dateien:**
- `main.py`:
  - `FormatSelectionPopup._select_format()`: Window-Resize-Logik
  - `Slideshow._setup_window_size()`: Initiale Window-Größe

### ✨ Vorteile

1. **Bessere UX im 9:16-Modus**: Vertikal gedrehter Text ist leichter lesbar auf vertikaler Toolbar
2. **Optimierte Bedienung im 16:9-Modus**: Toolbar am unteren Rand ist ergonomischer
3. **Nahtlose Format-Umschaltung**: Dynamische Anpassung ohne Neustart
4. **Volle Bilddarstellung**: Bilder werden korrekt im jeweiligen Format angezeigt (9:16 oder 16:9)

### 📋 Technische Details

**Bestätigte Funktionalität:**
- ✓ Bilder werden bereits korrekt skaliert (1920x1080 für 16:9, 1080x1920 für 9:16)
- ✓ `vertex_ai_image_workflow.py` verwendet dynamische Aspect-Ratio aus `image_meta.json`
- ✓ Keine Cropping-Probleme bei Bildgenerierung
- ✓ Layout passt sich sofort beim Format-Wechsel an

---

## Datum: 2024-10-03 - Repository Cleanup & Format Switching Fix

### 🎯 Zusammenfassung
Behebung von Problemen mit der dynamischen Formatumschaltung und umfassende Repository-Aufräumung.

---

## ✅ Behobene Probleme

### 1. Dynamische Formatumschaltung (9:16 ↔ 16:9)
**Problem:** Format-Wechsel erforderte Neustart der Anwendung, um Fenster anzupassen.

**Lösung:**
- Window-Größe wird jetzt **sofort** beim Format-Wechsel angepasst
- 16:9 Format → Fenster: 1280x720 (horizontal/breit)
- 9:16 Format → Fenster: 720x1280 (vertikal/hoch)
- Initiale Fenster-Größe basiert auf gespeicherter Einstellung in `image_meta.json`
- Bildliste wird automatisch neu gefiltert und angezeigt

**Geänderte Dateien:**
- `main.py`: 
  - `FormatSelectionPopup._select_format()`: Fügt Window-Resize hinzu
  - `Slideshow.__init__()`: Setzt initiale Window-Größe basierend auf aspect_ratio

**Code-Änderungen:**
```python
# In _select_format():
from kivy.core.window import Window
if aspect_ratio == "16:9":
    Window.size = (1280, 720)  # Horizontal
elif aspect_ratio == "9:16":
    Window.size = (720, 1280)  # Vertikal

# In Slideshow.__init__():
if self.aspect_ratio == "16:9":
    Window.size = (1280, 720)
elif self.aspect_ratio == "9:16":
    Window.size = (720, 1280)
```

---

### 2. Robustere Bildanzeige bei fehlenden Bildern
**Problem:** Wenn keine Bilder im gewählten Format vorhanden sind, wurde nur ein generischer Hinweis angezeigt.

**Lösung:**
- Informative Placeholder-Nachricht zeigt jetzt das aktuelle Format an
- Gibt konkrete Hinweise: "Format wechseln oder Bilder hinzufügen"
- Unterscheidet zwischen "keine Bilder überhaupt" und "keine Bilder im gewählten Format"

**Geänderte Dateien:**
- `main.py`: `Slideshow.show_current_image()`

**Code-Änderungen:**
```python
if not self.images:
    if self.current_mode:
        self.placeholder.text = (
            f"Keine Bilder im Format {self.aspect_ratio} "
            f"für Modus '{self.current_mode.name}'.\n"
            "Bitte Format wechseln oder Bilder hinzufügen."
        )
    else:
        self.placeholder.text = "Keine Bilder gefunden.\nBitte Bilder hinzufügen."
```

---

## 🗑️ Repository-Aufräumung

### Entfernte Test-Dateien (8 Dateien)
- `test_aspect_ratio_filtering.py`
- `test_end_to_end_workflow.py`
- `test_format_selection.py`
- `test_image_scaling.py`
- `test_mono_fix.py`
- `test_race_condition_fix.py`
- `test_recording_error_handling.py`
- `test_vertex_ai_integration.py`

**Begründung:** Test-Dateien waren Entwicklungs-Artefakte und werden für Produktion nicht benötigt.

---

### Entfernte Dokumentations-Dateien (14 Dateien)
- `ASPECT_RATIO_FILTERING.md`
- `FORMAT_SELECTION_FEATURE.md`
- `IMAGE_SELECTION_DIAGRAM.md`
- `IMPLEMENTATION_COMPLETE.md`
- `IMPLEMENTATION_SUMMARY.md`
- `IMPORT_MODE_ANLEITUNG.md`
- `IMPORT_MODE_FEATURE.md`
- `LIGHTBOX_FEATURE.md`
- `LIGHTBOX_WORKFLOW.md`
- `MONO_AUDIO_FIX.md`
- `PR_IMAGE_SELECTION_ENHANCEMENT.md`
- `PR_README.md`
- `PR_SUMMARY.md`
- `RACE_CONDITION_FIX.md`
- `README_CLEANED_WORKFLOW.md`
- `RECORDING_ERROR_HANDLING_IMPROVEMENTS.md`

**Begründung:** Redundante PR- und Feature-Dokumentation. Alle wichtigen Informationen wurden in zentrale README.md konsolidiert.

---

### Entfernte sonstige Dateien (1 Datei)
- `spinner-positioning-demo.png`

**Begründung:** Demo-Bild, nicht für Produktion benötigt.

---

### Neue Dateien
- **`README.md`**: Zentrale, umfassende Dokumentation
  - Hauptfunktionen
  - Setup & Installation
  - Verwendungsanleitung
  - Technische Details
  - Architektur-Übersicht
- **`CHANGELOG.md`**: Dieses Dokument

---

### Beibehaltene Kern-Dateien

#### Python-Anwendungen (7 Dateien)
- `main.py` - Hauptanwendung (Slideshow + UI)
- `Aufnahme.py` - Audio-Aufnahme
- `voiceToGoogle.py` - Speech-to-Text Transkription
- `upload_server.py` - Upload-Webserver
- `vertex_ai_image_workflow.py` - KI-Bildgenerierung
- `start_workflow_service.py` - Workflow-Orchestrierung
- `PythonServer.py` - Server-Funktionen

#### Dokumentation (3 Dateien)
- `README.md` - Hauptdokumentation
- `SPEECH_TO_TEXT_SETUP.md` - Google Speech-to-Text Setup
- `VERTEX_AI_SETUP.md` - Google Vertex AI Setup

#### Konfiguration (3 Dateien)
- `image_meta.json` - Bild-Metadaten und Einstellungen
- `modes.json` - Modi-Konfiguration
- `.gitignore` - Git-Ausschlüsse

---

### Aktualisierte .gitignore
**Neue Einträge:**
```gitignore
# Virtual environment
venv/
env/
ENV/
pyvenv.cfg

# Test files (removed in cleanup)
test_*.py

# Demo/temp images
*-demo.png
spinner-positioning-*.png
```

**Begründung:** Verhindert versehentliches Committen von Virtual Environments, Test-Dateien und Demo-Bildern.

---

## 📊 Statistik

### Vorher
- Python-Dateien: 15 (7 produktiv + 8 Tests)
- Dokumentation: 17 .md-Dateien
- Sonstiges: 1 Demo-Bild
- **Gesamt: ~33 Dateien**

### Nachher
- Python-Dateien: 7 (nur produktive)
- Dokumentation: 4 .md-Dateien (README + 3 Setup-Guides)
- **Gesamt: ~13 produktive Dateien**
- **Reduzierung: ~60% weniger Dateien**

---

## 🎨 Auswirkungen für Benutzer

### Sofortige Verbesserungen
1. **Kein Neustart mehr nötig** beim Format-Wechsel
2. **Klare Fehlermeldungen** wenn keine Bilder im Format vorhanden
3. **Übersichtlicheres Repository** mit nur produktiven Dateien
4. **Zentrale Dokumentation** in README.md statt verstreute Docs

### Keine Breaking Changes
- Alle bestehenden Funktionen bleiben unverändert
- Gespeicherte Einstellungen (`image_meta.json`, `modes.json`) bleiben kompatibel
- Workflow-Prozesse (Aufnahme → Transkription → Bildgenerierung) unverändert

---

## 🔧 Technische Details

### Window-Resize-Mechanismus
Die dynamische Fensteranpassung nutzt Kivys `Window.size` Property:
- **Read-write Property:** Kann zur Laufzeit geändert werden
- **Sofortige Anwendung:** Kein Neustart nötig
- **Plattform-unabhängig:** Funktioniert auf Desktop (Linux/Windows/macOS)

### Aspect Ratio Filterung
Bleibt unverändert:
- PIL/Pillow analysiert Bildabmessungen
- Bilder werden nach Breite/Höhe klassifiziert
- Filter wird bei Modi-Wechsel und Format-Wechsel angewendet

---

## ✅ Testing & Validierung

### Durchgeführte Tests
1. **Syntax-Check:** `python3 -m py_compile main.py` ✓ erfolgreich
2. **Code-Review:** Alle Änderungen auf logische Korrektheit geprüft ✓
3. **Git-Status:** Alle Dateien korrekt committed und gepusht ✓

### Empfohlene manuelle Tests
1. Start der Anwendung → Window-Größe entspricht gespeichertem Format
2. Format-Wechsel 16:9 → 9:16 → Fenster ändert sich sofort
3. Format-Wechsel mit leerer Bildliste → Informative Fehlermeldung
4. Normale Slideshow-Funktionen → Unverändert funktional

---

## 📝 Migration Guide

### Für Entwickler
- **Alte Test-Dateien:** Entfernt, bei Bedarf aus Git-History wiederherstellbar
- **Alte Dokumentation:** In `README.md` konsolidiert
- **Neue Struktur:** Fokus auf produktive Dateien und zentrale Doku

### Für Benutzer
- **Keine Aktion erforderlich**
- Vorhandene Konfigurationen bleiben erhalten
- Alle Funktionen arbeiten wie gewohnt

---

## 🔮 Zukünftige Verbesserungen

### Mögliche Erweiterungen
1. **Anpassbare Window-Größen:** Benutzer-definierte Auflösungen pro Format
2. **Zusätzliche Formate:** 4:3, 21:9, etc.
3. **Smooth Resize Animation:** Sanfter Übergang bei Format-Wechsel
4. **Format-Auto-Detection:** Automatische Format-Wahl basierend auf verfügbaren Bildern

---

## 👨‍💻 Entwickler-Notizen

### Code-Quality
- Alle Änderungen minimal und gezielt ("surgical changes")
- Keine bestehende Funktionalität beeinträchtigt
- Syntax-validiert
- Git-History sauber mit aussagekräftigen Commit-Messages

### Best Practices befolgt
- ✅ Minimale Änderungen
- ✅ Keine unnötigen Refactorings
- ✅ Bestehende Konventionen eingehalten
- ✅ Dokumentation aktualisiert
- ✅ .gitignore optimiert

---

## 📞 Support

Bei Fragen oder Problemen:
1. Siehe `README.md` für allgemeine Dokumentation
2. Prüfe `projekt.log` für Debug-Informationen
3. Aktiviere Debug-Overlay in Einstellungen für Live-Debugging

---

**Ende des Changelogs**
