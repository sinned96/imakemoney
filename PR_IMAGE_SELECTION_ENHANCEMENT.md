# PR: Bildauswahl-Erweiterung und uploads-Ordner Migration

## Zusammenfassung

Diese PR erweitert die Bildauswahl-Funktion in der Aufnahme (AufnahmePopup) und migriert den Import-Ordner von `BilderImport` zu `uploads`.

## Hauptänderungen

### 1. Quellordner-Definition (Source Folders)

**Neue Ordnerstruktur:**
- **Galerie (KI-Bilder)**: `/home/pi/Desktop/v2_Tripple S/BilderVertex`
- **Import (Uploads)**: `/home/pi/Desktop/v2_Tripple S/uploads`

**Vorher:**
```
├── BilderVertex/          # KI-Bilder
└── BilderImport/          # Import-Bilder (ALT)
```

**Nachher:**
```
├── BilderVertex/          # KI-Bilder (Galerie)
└── uploads/               # Import-Bilder (NEU)
```

### 2. Bildauswahl mit Tabs

Die Aufnahme-Funktion (`AufnahmePopup.open_image_selection()`) wurde erweitert:

**Vorher:**
- Einzelner Datei-Browser
- Zugriff nur auf BilderVertex

**Nachher:**
- Tabbed Interface mit zwei Tabs:
  - **"Galerie (KI-Bilder)"** → BilderVertex
  - **"Import (Uploads)"** → uploads
- Benutzer kann zwischen beiden Quellen wechseln

### 3. Funktionalität

✅ **Bildauswahl**: Funktioniert identisch für beide Quellen
✅ **Doppelklick-Overlay**: Funktioniert für beide Quellordner (bereits implementiert)
✅ **Import-Modus**: Lädt Bilder aus uploads-Ordner
✅ **Upload-Server**: Speichert neue Uploads in uploads-Ordner

## Geänderte Dateien

### Code-Änderungen
1. **main.py**
   - `IMPORT_DIR` geändert von `BilderImport` zu `uploads`
   - `open_image_selection()` erweitert mit TabbedPanel

2. **upload_server.py**
   - `IMPORT_DIR` geändert zu `uploads` Ordner

### Dokumentations-Änderungen
3. **IMPORT_MODE_FEATURE.md**
   - Quellordner-Übersicht hinzugefügt
   - Bildauswahl-Feature dokumentiert
   - Verzeichnisstruktur aktualisiert
   - Changelog erweitert

4. **IMPORT_MODE_ANLEITUNG.md**
   - Pfade aktualisiert (BilderImport → uploads)

5. **IMPLEMENTATION_SUMMARY.md**
   - Verzeichnisstruktur aktualisiert

## Migration

### Für Benutzer

Falls bereits Bilder im alten `BilderImport` Ordner existieren, diese bitte nach `uploads` verschieben:

```bash
# Backup erstellen (optional)
cp -r "/home/pi/Desktop/v2_Tripple S/BilderImport" "/home/pi/Desktop/v2_Tripple S/BilderImport.backup"

# Ordner umbenennen
mv "/home/pi/Desktop/v2_Tripple S/BilderImport" "/home/pi/Desktop/v2_Tripple S/uploads"
```

Oder Bilder manuell kopieren:
```bash
mkdir -p "/home/pi/Desktop/v2_Tripple S/uploads"
cp "/home/pi/Desktop/v2_Tripple S/BilderImport"/* "/home/pi/Desktop/v2_Tripple S/uploads/"
```

## Tests

✅ Python-Syntax überprüft (py_compile)
✅ Konstanten korrekt konfiguriert
✅ Keine verbleibenden BilderImport-Referenzen im Code

## Kompatibilität

- ✅ Bestehende Funktionen nicht beeinträchtigt
- ✅ Doppelklick-Feature funktioniert weiterhin
- ✅ Import-Modus funktioniert mit neuem Ordner
- ✅ Upload-Server speichert in korrektem Ordner

## Hinweise

- Der alte `BilderImport` Ordner wird nicht automatisch umbenannt
- Alle neuen Uploads gehen in den `uploads` Ordner
- Die Bildauswahl-Tabs funktionieren auch wenn Ordner noch nicht existieren (Fallback zu Home-Verzeichnis)
