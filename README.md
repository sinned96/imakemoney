# ImakeMoney - Slideshow & AI Image Management System

Eine Kivy-basierte Slideshow-Anwendung mit KI-Bildgenerierung, Audio-zu-Text-Transkription und dynamischer Formatumschaltung.

## Hauptfunktionen

### 🖼️ Bildverwaltung & Slideshow
- **Dynamische Formatumschaltung**: Sofortiger Wechsel zwischen 16:9 (Horizontal) und 9:16 (Vertikal) Format
- **Automatische Bildfilterung**: Zeigt nur Bilder im gewählten Format an
- **Effekte**: Fade, Slide, Zoom, Pan, Rotate, Blitz
- **Modi**: Tag/Nacht-Modi mit Zeitsteuerung, Import-Modus für hochgeladene Bilder
- **Galerie-Editor**: Bilder auswählen, Einstellungen pro Bild (Effekte, Intervalle, Helligkeit)

### 🎙️ Audio & Transkription
- **Aufnahme-Funktion**: Audio-Aufnahme mit automatischer Transkription via Google Speech-to-Text
- **Mono-Audio-Optimierung**: Automatische Konvertierung zu Mono für optimale API-Kompatibilität
- **Text-Output**: Transkripte werden als .txt und .json gespeichert

### 🤖 KI-Integration
- **Vertex AI**: Automatische Bildgenerierung basierend auf Audio-Transkriptionen
- **Workflow Service**: Hintergrundprozess für asynchrone Bildgenerierung
- **Upload-Server**: Webserver für Bildupload von anderen Geräten

### 🔐 Authentifizierung
- Login/Register-System mit verschlüsselten Passwörtern
- Benutzerverwaltung mit Firma, Name, Email

## Setup & Installation

### Voraussetzungen
```bash
pip install kivy kivymd pillow qrcode google-cloud-speech google-cloud-aiplatform
```

### Google Cloud Setup
1. **Speech-to-Text API**: Siehe `SPEECH_TO_TEXT_SETUP.md` für Details
2. **Vertex AI**: Siehe `VERTEX_AI_SETUP.md` für Konfiguration
3. Service-Account-Key in `cloudKey.json` speichern

### Konfiguration
Wichtige Pfade in `main.py`:
- `IMAGE_DIR`: Verzeichnis für KI-generierte Bilder (`BilderVertex`)
- `IMPORT_DIR`: Verzeichnis für importierte Bilder (`uploads`)
- `ACCOUNTS_PATH`: Benutzerdatenbank
- `MODES_PATH`: Modi-Konfiguration (`modes.json`)

## Verwendung

### Start
```bash
python main.py
```

### Format-Umschaltung
1. Klicke auf das Format-Icon (aspect-ratio) in der Toolbar
2. Wähle "Horizontal (16:9)" oder "Vertikal (9:16)"
3. **Fenster und Bilder passen sich SOFORT an** - kein Neustart nötig!

### Aufnahme & Bildgenerierung
1. Klicke auf das Aufnahme-Icon (record) in der Toolbar
2. Nimm Audio auf oder wähle eine Audiodatei
3. Text wird transkribiert und KI-Bild generiert
4. Bild erscheint automatisch in der Galerie

### Bildupload
1. Upload-Server läuft automatisch im Hintergrund
2. Greife über Netzwerk-IP auf Webinterface zu
3. Lade Bilder hoch - sie erscheinen im Import-Modus

## Funktionen im Detail

### Formatfilterung
- Bilder werden automatisch nach Seitenverhältnis analysiert (PIL/Pillow)
- Nur passende Bilder werden im gewählten Format angezeigt
- Hinweis: "Keine passenden Bilder gefunden" wenn keine Bilder im Format vorhanden

### Modi & Scheduling
- **Standard/Alle Bilder**: Alle KI-generierten Bilder
- **Import**: Hochgeladene/importierte Bilder
- **Tag/Nacht-Modi**: Zeitgesteuerte Bildauswahl mit Zeitfenstern
- Automatischer Moduswechsel basierend auf Tageszeit

### Galerie-Editor
- Miniaturansicht aller Bilder
- Filter: Nur ausgewählte Bilder anzeigen
- Pro Bild konfigurierbar:
  - Effekt-Override
  - Intervall-Override
  - Helligkeits-Override
  - Prioritäts-Gewichtung

### Einstellungen
- Globale Effekte auswählen
- Effekte randomisieren
- Globales Intervall
- Globale Helligkeit
- Debug-Overlay ein/aus

## Technische Details

### Bildeffekte
- **Fade**: Sanftes Ein-/Ausblenden
- **Slide**: Links/Rechts-Sliding
- **Zoom In**: Zoom-Effekt mit Skalierung
- **Zoom+Pan**: Zoom mit Pan-Bewegung
- **Rotate**: Rotation während Übergang
- **Blitz**: Kurzer Weißblitz-Effekt

### Persistenz
- `image_meta.json`: Speichert Effekte, Intervalle, Gewichtungen, Helligkeit, Format
- `modes.json`: Modi-Konfiguration mit Zeitfenstern

### Fehlerbehandlung
- Robuste Bildanzeige mit Fallback bei fehlenden Bildern
- Logging in `projekt.log`
- Debug-Overlay zeigt aktuelle Bild-Info

## Architektur

### Hauptkomponenten
- **KioskMDApp**: Hauptanwendung mit Login-System
- **Slideshow**: Kern-Widget für Bildanzeige und Steuerung
- **AufnahmePopup**: Aufnahme-Dialog mit Transkription
- **GalleryEditor**: Galerie-Verwaltung
- **FormatSelectionPopup**: Format-Auswahl-Dialog
- **ModeManager**: Modi-Verwaltung und Scheduling

### Hintergrundservices
- **upload_server.py**: Flask-Server für Bildupload
- **vertex_ai_image_workflow.py**: KI-Bildgenerierung
- **start_workflow_service.py**: Workflow-Orchestrierung

## Portrait Matrix Pipeline - Diagnostics & Configuration

### Environment Variables for Raspberry Pi / Portrait Mode

#### Pipeline Selection
- **PORTRAIT_PIPELINE** - Choose rendering pipeline (default: auto-detected)
  - `matrix` - Matrix-based rotation (default, reliable on most systems)
  - `fbo` - FBO-based rendering with letterboxing (auto-selected on Broadcom V3D/RPi)
  - `off` - Disable portrait rotation entirely (landscape mode)

- **PORTRAIT_FORCE_FBO=1** - Force FBO pipeline regardless of hardware
- **PORTRAIT_FORCE_MATRIX=1** - Force matrix pipeline regardless of hardware

#### Matrix Implementation
- **PORTRAIT_MATRIX_IMPL** - Matrix implementation mode (default: `mi`)
  - `mi` - MatrixInstruction (single matrix, default)
  - `rt` - Rotate/Translate/Scale (explicit instructions, better V3D compatibility)

#### Rotation Settings
- **PORTRAIT_ROTATION_DEGREES** - Rotation angle (default: `-90`)
  - `-90` - Counterclockwise (left rotation)
  - `90` - Clockwise (right rotation)
  - `0` - No rotation

- **PORTRAIT_SCALE_FIT** - Scale content to fit window (default: `1`)
  - `1` - Enable scaling (recommended)
  - `0` - Disable scaling

#### Debug Overlays
- **DEBUG_ROTATION_OVERLAY=1** - Show rotation diagnostics (magenta fill, green border, crosshair)
- **DEBUG_TOP_OVERLAY=1** - Show top-most diagnostic banner
- **DEBUG_FORCE_LOGIN_SIZE=1** - Force LoginScreen to known size for testing
- **DEBUG_AUTO_SCREENSHOT=1** - Take screenshot on first rendered frame
- **DEBUG_LOGIN_PAINT=1** - Add colored rectangle to LoginScreen
- **DEBUG_WINDOW_OVERLAY=1** - Show Window-level debug overlay (red overlay + banner)
- **DEBUG_FRAME_CORNERS=1** - Show colored corner markers in virtual portrait space (red=top-left, green=top-right, blue=bottom-right, yellow=bottom-left)

### Running Diagnostics
When troubleshooting portrait mode (9:16) rendering issues on Raspberry Pi, use these diagnostic tools:

#### Default (auto-detect, with diagnostics)
```bash
python3 main.py
```
**Expected behavior:**
- Auto-detects Broadcom V3D and uses FBO pipeline
- Magenta semi-transparent test fill covers the portrait area
- Green border (4px) outlines the virtual content area (1080x1920)
- Yellow crosshair at center of portrait area
- Orange banner showing "DIAG: FORCED LOGIN SIZE" (if force-size enabled)
- LoginScreen should be visible and rotated left
- Logs show per-frame child geometry for first 8 frames

#### Test Window overlay (above everything)
```bash
DEBUG_WINDOW_OVERLAY=1 python3 main.py
```
Shows a red semi-transparent overlay with "DEBUG WINDOW OVERLAY" banner.
This verifies GL draw state is working even if app content is black.

#### Force matrix pipeline with RT implementation (RPi-friendly)
```bash
PORTRAIT_PIPELINE=matrix PORTRAIT_MATRIX_IMPL=rt python3 main.py
```
Uses explicit Rotate/Translate/Scale instructions instead of MatrixInstruction.
Better compatibility with Broadcom V3D drivers.

#### Force FBO pipeline
```bash
PORTRAIT_FORCE_FBO=1 python3 main.py
```
Forces FBO-based rendering with letterboxing (legacy mode).

#### Disable forced LoginScreen size
```bash
DEBUG_FORCE_LOGIN_SIZE=0 python3 main.py
```
Use this to test if LoginScreen has natural size=(0,0) issues.

#### Hide diagnostic overlays
```bash
DEBUG_ROTATION_OVERLAY=0 DEBUG_TOP_OVERLAY=0 python3 main.py
```
Hides magenta fill, borders, and banner for clean testing.

#### Baseline comparison (landscape mode)
```bash
PORTRAIT_PIPELINE=off python3 main.py
```
Tests in standard 16:9 landscape mode without rotation.

#### Custom rotation angle
```bash
PORTRAIT_ROTATION_DEGREES=90 python3 main.py
```
Rotate clockwise (right) instead of counterclockwise (left).

### Diagnostic Logs
Check `projekt.log` for:
- `[Portrait matrix] Frame N: X children: [ClassNames] sizes=[...]` - Child widget geometry
- `[Portrait matrix] WARNING: WidgetName has size 0x0` - Zero-size widget warnings
- `[Portrait matrix] event=1920x1080 s=1.0000 pos=(0,0) rot=-90` - Transform details
- `[Portrait matrix] Forced size for LoginScreen: size=(1080,1920) pos=(0,0)` - Force-size confirmation

### Acceptance Criteria
✅ Magenta test fill and green border visible in portrait area  
✅ LoginScreen becomes visible (with forced size) or logs show 0x0 sizes  
✅ Logs include per-frame child count and geometry for first 8 frames  
✅ Logs include warnings for any child with size=(0,0)  
✅ No crashes; touch continues to work  

## Bekannte Einschränkungen
- PIL/Pillow erforderlich für Formatfilterung
- Google Cloud Credentials erforderlich für KI-Features
- Quadratische Bilder werden dem aktuellen Format zugeordnet

## Support & Entwicklung
Bei Fragen oder Problemen, siehe die Logs in `projekt.log` oder aktiviere das Debug-Overlay in den Einstellungen.
