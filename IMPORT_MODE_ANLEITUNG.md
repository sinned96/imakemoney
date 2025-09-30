# Import-Modus: Benutzeranleitung

## Übersicht

Der Import-Modus ist eine neue Funktion, die importierte Bilder separat von KI-generierten Bildern verwaltet. Alle Bilder können durch Doppelklick oder Doppeltipp in Originalgröße angezeigt werden.

## Neue Funktionen

### 🗂️ Separater Import-Ordner

Bilder werden jetzt in zwei verschiedenen Ordnern gespeichert:

- **KI-Bilder**: `/home/pi/Desktop/v2_Tripple S/BilderVertex`
- **Import-Bilder**: `/home/pi/Desktop/v2_Tripple S/BilderImport`

### 📱 Import-Button in der Modi-Liste

In der Galerie gibt es jetzt einen neuen Button **"Import"** in der linken Seitenleiste unter "Modi". Beim Klick darauf werden nur die importierten Bilder angezeigt.

**Verfügbare Modi:**
- Tag
- Nacht
- Urlaub
- **Import** ← **NEU!**

### 🖼️ Vollbild-Ansicht (Doppelklick/Doppeltipp)

Alle Bilder (KI und Import) können nun in Vollgröße angezeigt werden:

#### Desktop (mit Maus):
1. Öffne die Galerie
2. Doppelklick auf ein beliebiges Bild
3. ➡️ Das Bild wird in einem Overlay in Originalgröße angezeigt
4. Schließen: ✕-Button oben rechts oder Klick auf den dunklen Hintergrund

#### Mobile (Touch):
1. Öffne die Galerie
2. Zweimal schnell auf ein Bild tippen (Doppeltipp)
3. ➡️ Das Bild wird in einem Overlay in Originalgröße angezeigt
4. Schließen: Touch auf den dunklen Hintergrund

**Features der Vollbild-Ansicht:**
- ✅ Originalgröße (kein Upscaling)
- ✅ Seitenverhältnis beibehalten
- ✅ Zentrierte Anzeige
- ✅ Dateiname wird angezeigt
- ✅ Funktioniert für alle Bilder (KI und Import)

## Verwendung

### Import-Modus aktivieren

```
1. Öffne die Galerie
   │
   ├─ Linke Seitenleiste: "Modi"
   │
   └─ Klick auf "Import"
      │
      └─ ✅ Nur importierte Bilder werden angezeigt
```

### Bilder importieren

#### Über Mobile Upload (QR-Code):
```
1. QR-Code scannen (in der App verfügbar)
   │
   ├─ Öffnet Upload-Seite im Browser
   │
   ├─ Bilder auswählen
   │
   └─ Hochladen
      │
      └─ ✅ Bilder erscheinen automatisch im Import-Ordner
```

#### Direkt über den Upload-Server:
```
1. Browser öffnen
   │
   ├─ http://[IP-Adresse]:8000/upload
   │
   ├─ Bilder per Drag & Drop oder Auswahl hochladen
   │
   └─ ✅ Bilder werden im Import-Ordner gespeichert
```

### Bilder in Vollbild anzeigen

```
Desktop:                          Mobile:
───────────────────────          ───────────────────────
Galerie öffnen                   Galerie öffnen
    │                                │
Bild finden                      Bild finden
    │                                │
Doppelklick auf Bild             Zweimal schnell tippen
    │                                │
    └─────────┬──────────────────────┘
              │
         Overlay öffnet sich
              │
    ┌─────────┴─────────┐
    │                   │
✕-Button           Hintergrund
(oben rechts)      klicken/tippen
    │                   │
    └─────────┬─────────┘
              │
         Schließen
```

## Beispiele

### Beispiel 1: Import-Bilder anzeigen

```
Schritt 1: Galerie öffnen
Schritt 2: Modi-Liste → "Import" klicken
Schritt 3: ✅ Nur importierte Bilder werden angezeigt

Hinweis: Andere Modi (Tag, Nacht) zeigen weiterhin KI-Bilder
```

### Beispiel 2: Bild in Vollgröße öffnen

```
Desktop:
  1. Mauszeiger über ein Bild bewegen
  2. Schnell zweimal klicken (Doppelklick)
  3. ✅ Bild öffnet sich in Vollgröße

Mobile:
  1. Finger auf ein Bild legen
  2. Schnell zweimal antippen (Doppeltipp)
  3. ✅ Bild öffnet sich in Vollgröße

Wichtig: 
  - Zeit zwischen Klicks/Tipps: < 0.3 Sekunden
  - Nur auf dem Bild selbst, nicht auf den Buttons
```

## Häufige Fragen (FAQ)

### ❓ Wo werden importierte Bilder gespeichert?

**Antwort:** In einem separaten Ordner:
- Import-Bilder: `/home/pi/Desktop/v2_Tripple S/BilderImport`
- KI-Bilder: `/home/pi/Desktop/v2_Tripple S/BilderVertex`

### ❓ Wie erkenne ich importierte Bilder?

**Antwort:** Dateinamen beginnen mit `import_`:
- Beispiel: `import_20240115_123456_photo.jpg`

### ❓ Funktioniert der Doppelklick auf allen Bildern?

**Antwort:** Ja! Das Feature funktioniert für:
- ✅ KI-generierte Bilder
- ✅ Importierte Bilder
- ✅ Alle Modi (Tag, Nacht, Urlaub, Import)

### ❓ Was passiert, wenn ich zu schnell klicke?

**Antwort:** Das ist kein Problem! Die Doppelklick-Erkennung ist stabil:
- Zwei schnelle Klicks: Bild öffnet sich
- Drei schnelle Klicks: Keine Reaktion (verhindert)
- Nach dem Öffnen wird der Zähler zurückgesetzt

### ❓ Kann ich das Bild vergrößern (Zoom)?

**Antwort:** Aktuell nicht implementiert. Das Bild wird in Originalgröße angezeigt (maximal 90% der Bildschirmgröße), behält aber immer sein Seitenverhältnis.

### ❓ Können Import-Bilder in anderen Modi verwendet werden?

**Antwort:** Ja! In der Galerie kannst Du:
1. Import-Modus wählen
2. Bilder auswählen
3. Diese zu anderen Modi (Tag, Nacht, etc.) hinzufügen

## Fehlerbehebung

### Problem: Import-Button fehlt

**Lösung:** 
1. Programm schließen
2. Datei `modes.json` im App-Verzeichnis löschen
3. Programm neu starten → Import-Modus wird automatisch erstellt

### Problem: Doppelklick funktioniert nicht

**Mögliche Ursachen:**
1. ❌ Zu langsam geklickt (> 0.3 Sekunden)
   - ✅ Lösung: Schneller klicken
   
2. ❌ Auf Button geklickt statt auf Bild
   - ✅ Lösung: Direkt auf das Bild klicken
   
3. ❌ Programm nicht neu gestartet nach Update
   - ✅ Lösung: Programm neu starten

### Problem: Importierte Bilder werden nicht angezeigt

**Lösung:**
1. Prüfe, ob Bilder im Import-Ordner existieren:
   ```bash
   ls -la "/home/pi/Desktop/v2_Tripple S/BilderImport"
   ```
2. Im Import-Modus: Galerie neu laden (Modus wechseln und zurück)
3. Prüfe Dateiendungen (nur .jpg, .jpeg, .png werden unterstützt)

### Problem: Upload schlägt fehl

**Lösung:**
1. Prüfe, ob Upload-Server läuft
2. Prüfe Internet-Verbindung
3. Prüfe Logs in `projekt.log`
4. Versuche, den Server neu zu starten

## Technische Hinweise

### Unterstützte Bildformate
- `.jpg` / `.jpeg`
- `.png`

### Performance
- Maximale Anzahl angezeigter Bilder: 2000
- Optimiert für Touch- und Desktop-Geräte
- Keine Auswirkung auf die Geschwindigkeit der Slideshow

### Sicherheit
- Upload-Server prüft Dateitypen
- Dateinamen werden automatisch gesichert (Timestamp)
- Originalbilder werden nicht verändert

## Support

Bei Problemen oder Fragen:
1. Logs prüfen: `projekt.log`
2. Dokumentation lesen: `IMPORT_MODE_FEATURE.md` (Technisch)
3. Lightbox-Details: `LIGHTBOX_FEATURE.md`

---

**Version:** 1.0  
**Datum:** 2025-01-15  
**Status:** ✅ Voll funktionsfähig
