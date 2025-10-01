# Import Mode Feature Documentation

## Übersicht

Dieses Feature fügt einen neuen "Import"-Modus zur Galerie hinzu, der importierte Bilder separat von KI-generierten Bildern verwaltet und anzeigt. Alle Bilder (KI und Import) unterstützen das Doppelklick-/Doppeltipp-Feature zur Vollbildanzeige.

### Quellordner-Übersicht (Source Folders)
- **Galerie**: `/home/pi/Desktop/v2_Tripple S/BilderVertex` - KI-generierte Bilder
- **Import**: `/home/pi/Desktop/v2_Tripple S/uploads` - Importierte Bilder (via Mobile Upload oder Aufnahme-Funktion)

## Funktionen

### 1. Import-Ordner (uploads)

- Separater Ordner für importierte Bilder: `/home/pi/Desktop/v2_Tripple S/uploads`
- KI-generierte Bilder bleiben im ursprünglichen Ordner: `/home/pi/Desktop/v2_Tripple S/BilderVertex`
- Klare Trennung zwischen importierten und generierten Bildern

### 2. Import-Modus in der Galerie

- Neuer Button "Import" in der Modi-Liste (linke Seite)
- Zeigt ausschließlich importierte Bilder aus dem Import-Ordner an
- Funktioniert analog zu anderen Modi wie "Tag", "Nacht" und "Urlaub"
- Beim Wechseln zum Import-Modus werden automatisch die Bilder aus dem Import-Ordner geladen

### 3. Doppelklick-/Doppeltipp-Feature

Das Feature ist bereits vollständig implementiert und funktioniert für **alle Bilder**:

#### Desktop (Maus)
- Doppelklick auf ein Bild öffnet es im Lightbox-Overlay
- Bildgröße: Original-Seitenverhältnis beibehalten, maximal 90% der Fenstergröße
- Schließen: ✕-Button oder Klick auf dunklen Hintergrund

#### Touch-Geräte (Smartphone/Tablet)
- Doppeltipp auf ein Bild öffnet es im Lightbox-Overlay
- Gleiche Darstellung wie auf Desktop
- Touch auf Hintergrund schließt das Overlay

#### Technische Details
- Zeitfenster für Doppelklick: 0.3 Sekunden
- Funktioniert nur auf dem Bildsymbol (nicht auf Buttons)
- Reset nach Doppelklick verhindert Dreifach-Klick-Erkennung
- Stabile Implementierung ohne Aufhängen

### 4. Upload-Server Integration

- Mobile Uploads werden automatisch im Import-Ordner gespeichert
- Dateinamen-Präfix geändert von `upload_` zu `import_`
- Format: `import_YYYYMMDD_HHMMSS_originalname.ext`

### 5. Bildauswahl mit Tabs (Aufnahme-Funktion)

- Beim Hinzufügen eines Bildes zur Aufnahme gibt es jetzt zwei Tabs:
  - **"Galerie (KI-Bilder)"**: Zugriff auf BilderVertex-Ordner
  - **"Import (Uploads)"**: Zugriff auf uploads-Ordner
- Benutzer können zwischen beiden Quellen wechseln
- Identische Funktionalität für beide Bildquellen

## Technische Implementierung

### Konstanten

```python
IMAGE_DIR = Path("/home/pi/Desktop/v2_Tripple S/BilderVertex")  # KI-Bilder (Galerie)
IMPORT_DIR = Path("/home/pi/Desktop/v2_Tripple S/uploads")      # Import-Bilder
```

### ModeManager

Der Import-Modus wird automatisch beim ersten Start erstellt:

```python
def ensure_defaults(self):
    # ...
    if "Import" not in names:
        self.modes.append(Mode("Import", images=[], interval=5, windows=[], auto=False))
```

### Slideshow

Neue Methode zum Scannen importierter Bilder:

```python
def _scan_import(self):
    """Scan IMPORT_DIR for imported images"""
    if IMPORT_DIR.exists():
        files=[str(p) for p in IMPORT_DIR.iterdir() 
               if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        files.sort()
        return files
    return []
```

Der Import-Modus wird in `set_mode()` und `_check_new_files()` behandelt:

```python
if mode.name == "Import":
    self.images = self._scan_import()
```

### GalleryEditor

Die Galerie lädt automatisch Bilder aus dem richtigen Ordner basierend auf dem gewählten Modus:

```python
def _reload_all_images(self):
    """Load images from appropriate directory based on current mode"""
    if self.target_mode and self.target_mode.name == "Import":
        # Load from IMPORT_DIR
        if IMPORT_DIR.exists():
            files = [str(p) for p in IMPORT_DIR.iterdir() 
                    if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    else:
        # Load from standard IMAGE_DIR
        if IMAGE_DIR.exists():
            files = [str(p) for p in IMAGE_DIR.iterdir() 
                    if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
```

### ImageTile (Doppelklick-Erkennung)

```python
def on_touch_down(self, touch):
    """Handle touch/click events for double-click/tap detection"""
    if self.img.collide_point(*touch.pos):
        current_time = time.time()
        time_since_last = current_time - self.last_touch_time
        
        if time_since_last < self.double_click_threshold:
            # Double-click detected! Open lightbox
            self._open_lightbox()
            self.last_touch_time = 0
            return True
        else:
            self.last_touch_time = current_time
    
    return super().on_touch_down(touch)
```

### ImageLightboxPopup (Vollbildanzeige)

```python
class ImageLightboxPopup(FloatLayout):
    """Lightbox overlay for displaying full-size images"""
    def __init__(self, image_path, **kw):
        # Dark overlay background (90% opacity)
        # Full-size image centered on screen
        # Close button (top-right)
        # Filename label (bottom)
        # Click anywhere on background to close
```

## Verwendung

### Galerie öffnen und Import-Modus wählen

1. Öffne die Galerie
2. In der linken Seitenleiste unter "Modi" auf "Import" klicken
3. Die Galerie zeigt jetzt nur importierte Bilder an

### Bilder importieren (Mobile Upload)

1. Server starten (automatisch oder manuell)
2. QR-Code scannen oder Upload-URL öffnen
3. Bilder hochladen
4. Bilder werden automatisch im Import-Ordner gespeichert
5. Im Import-Modus der Galerie sichtbar

### Bilder in Vollbild anzeigen

1. In der Galerie ein beliebiges Bild finden
2. **Desktop:** Doppelklick auf das Bild
3. **Mobile:** Zweimal schnell auf das Bild tippen
4. Das Bild wird in Originalgröße im Overlay angezeigt
5. **Schließen:** ✕-Button oder Klick/Touch auf den dunklen Hintergrund

## Kompatibilität

- ✅ Desktop (Maus-Doppelklick)
- ✅ Touch-Geräte (Doppeltipp)
- ✅ KI-generierte Bilder
- ✅ Importierte Bilder
- ✅ Alle Modi (Tag, Nacht, Urlaub, Import)

## Verzeichnisstruktur

```
/home/pi/Desktop/v2_Tripple S/
├── BilderVertex/          # KI-generierte Bilder (Galerie)
│   ├── bild_001.png
│   ├── bild_002.png
│   └── ...
├── uploads/               # Importierte Bilder (Import-Ordner)
│   ├── import_20240115_123456_photo1.jpg
│   ├── import_20240115_123457_photo2.jpg
│   └── ...
├── transkript.json
└── projekt.log
```

## Bekannte Einschränkungen

1. **Nur auf Bild-Bereich:** Doppelklick funktioniert nur auf dem Bildbereich, nicht auf den Buttons
2. **Zeitfenster:** Zwischen den Klicks/Tipps müssen < 0.3 Sekunden liegen
3. **Keine Zoom-Funktion:** Aktuell nicht implementiert (mögliches zukünftiges Feature)

## Changelog

### Version 2.0 (2025-01-XX)
- ✅ IMPORT_DIR geändert von `BilderImport` zu `uploads` Ordner
- ✅ Bildauswahl-Popup erweitert mit Tabs für Galerie (BilderVertex) und Import (uploads)
- ✅ Upload-Server speichert jetzt in uploads-Ordner
- ✅ Dokumentation aktualisiert: Galerie = BilderVertex, Import = uploads

### Version 1.0 (2025-01-15)
- ✅ IMPORT_DIR Konstante hinzugefügt
- ✅ Import-Modus in ModeManager defaults
- ✅ GalleryEditor lädt aus IMPORT_DIR für Import-Modus
- ✅ Slideshow behandelt Import-Modus mit _scan_import()
- ✅ Upload-Server speichert in IMPORT_DIR
- ✅ Doppelklick-/Doppeltipp-Feature für alle Bilder
- ✅ ImageLightboxPopup für Vollbildanzeige

## Support

Bei Fragen oder Problemen:
1. Siehe `LIGHTBOX_FEATURE.md` für Details zur Lightbox-Funktion
2. Siehe `LIGHTBOX_WORKFLOW.md` für technische Workflow-Details
3. Prüfe die Logdatei `projekt.log` für Fehlermeldungen
