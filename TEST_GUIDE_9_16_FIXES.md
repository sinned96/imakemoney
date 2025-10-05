# Test Guide: 9:16 End-to-End Fixes

Diese Anleitung hilft beim Testen der 9:16-End-to-End-Fixes (Workflow-Skalierung, Menüausrichtung, Doppelklick-Hänger).

## Übersicht der Fixes

1. **Workflow-Skalierung**: 9:16-Bilder werden nicht mehr auf 16:9 (1920x1080) gezwungen
2. **Menü-Rotation**: Text im 9:16-Modus ist jetzt 90° gedreht (vertikal, von unten nach oben lesbar)
3. **Doppelklick-Hänger**: Debounce und is_lightbox_open Flag verhindern App-Freeze

---

## Test 1: 9:16 Bildgenerierung und Workflow

### Ziel
Verifizieren, dass generierte 9:16-Bilder das korrekte Format (1080x1920) haben und nicht auf 16:9 skaliert werden.

### Voraussetzungen
- `image_meta.json` existiert im Projektverzeichnis
- `aspect_ratio` ist auf `"9:16"` gesetzt

### Schritte

1. **Konfiguration prüfen**
   ```bash
   cat image_meta.json
   # Sollte enthalten: "aspect_ratio": "9:16"
   ```

2. **Projekt starten und 9:16-Modus aktivieren**
   - App starten: `python3 main.py`
   - Im UI: Format-Button → "Vertikal 9:16" auswählen
   - Bestätigen, dass `image_meta.json` jetzt `"aspect_ratio": "9:16"` enthält

3. **Bild generieren**
   - "Aufnahme"-Button klicken
   - Sprachaufnahme machen oder Prompt eingeben
   - Warten bis Bildgenerierung abgeschlossen ist

4. **Ergebnis überprüfen**
   ```bash
   # Bildgröße prüfen
   cd "/home/pi/Desktop/v2_Tripple S/BilderVertex"
   file bild_*.png | tail -1
   # Sollte zeigen: 1080 x 1920 (NICHT 1920 x 1080)
   
   # Oder mit Python
   python3 -c "from PIL import Image; img=Image.open('bild_XX.png'); print(f'Größe: {img.size}')"
   # Sollte zeigen: Größe: (1080, 1920)
   ```

5. **Logs überprüfen**
   ```bash
   tail -50 "/home/pi/Desktop/v2_Tripple S/projekt.log" | grep -i "scaling\|aspect"
   ```
   
   **Erwartete Log-Einträge:**
   ```
   [INFO] Aspect ratio from image_meta.json: 9:16
   [INFO] Scaling image: aspect_ratio=9:16, input_size=(768, 1408), output_size=(1080, 1920)
   [INFO] Image scaled to 1080x1920 with aspect ratio preserved: (768, 1408) -> (1080, 1920)
   ```

### ✅ Erfolgskriterien
- [ ] image_meta.json enthält `"aspect_ratio": "9:16"`
- [ ] Generiertes Bild hat Dimensionen 1080x1920 (nicht 1920x1080)
- [ ] Logs zeigen `aspect_ratio=9:16` und `output_size=(1080, 1920)`
- [ ] Keine Weißflächen oder falsche Skalierung im Log

### ❌ Fehlerbehandlung
- **Problem**: Bild ist immer noch 1920x1080
  - **Lösung**: Prüfe ob `PythonServer.py` die neueste Version hat
  - Stelle sicher dass `scale_image_to_1920x1080()` aspect_ratio aus image_meta.json liest
  
- **Problem**: Log zeigt "Could not read aspect ratio from image_meta.json"
  - **Lösung**: Prüfe Dateipfad und -berechtigungen von image_meta.json

---

## Test 2: 9:16 Bildanzeige ohne Weißflächen

### Ziel
Verifizieren, dass 9:16-Bilder korrekt im Content-Container angezeigt werden ohne weiße Ränder.

### Schritte

1. **App im 9:16-Modus starten**
   - `python3 main.py`
   - Format → "Vertikal 9:16"

2. **Bild laden/anzeigen**
   - Entweder Slideshow läuft automatisch
   - Oder Galerie → Bild auswählen

3. **Visuelle Inspektion**
   - Prüfen: Bild füllt den linken Bereich (ohne Toolbar-Breite)
   - Prüfen: KEINE weißen Ränder oben/unten/links
   - Prüfen: Bild ist zentriert im verfügbaren Content-Bereich
   - Prüfen: Toolbar (110px breit) ist rechts und überlappt nicht mit Bild

4. **Debug-Logs prüfen**
   ```bash
   tail -30 "/home/pi/Desktop/v2_Tripple S/projekt.log" | grep -i "9:16 mode\|content="
   ```
   
   **Erwartete Log-Einträge:**
   ```
   [DEBUG] 9:16 mode: window=1920x1080, toolbar_width=110, content=1810x1080
   [DEBUG] cover mode: texture=1080x1920, scale=1.68, img size=1814x3226, pos=(-2, -1073)
   ```
   
   Hinweis: Im `cover` Modus ist es normal dass das Bild größer als der Container ist und negative Positionen hat (Zentrierung).

### ✅ Erfolgskriterien
- [ ] Kein weißer Hintergrund sichtbar
- [ ] Bild ist zentriert und füllt Content-Bereich
- [ ] Toolbar überlappt nicht mit Bild
- [ ] Content-Breite = Fensterbreite - 110px (Toolbar)

### ❌ Fehlerbehandlung
- **Problem**: Weißer Hintergrund sichtbar
  - **Lösung**: Prüfe ob `keep_ratio=True` in Slideshow.__init__() gesetzt ist
  - Prüfe ob Hintergrund-Canvas Color auf (0.02, 0.02, 0.03, 1) gesetzt ist

---

## Test 3: Menü-Textrotation (9:16-Modus)

### Ziel
Verifizieren, dass Menü-Buttons im 9:16-Modus korrekt rotiert sind (90°, von unten nach oben lesbar).

### Schritte

1. **App im 9:16-Modus starten**
   - `python3 main.py`
   - Format → "Vertikal 9:16"

2. **Visuelle Inspektion der Toolbar (rechts)**
   - Toolbar sollte auf der rechten Seite sein (vertikal)
   - Button-Texte: "Zeiten", "Aufnahme", "Format", "Galerie", "Settings", "Logout", "Exit"

3. **Text-Ausrichtung prüfen**
   - Text sollte **90° gedreht** sein (vertikal)
   - Text sollte **von unten nach oben lesbar** sein
   - Drehe deinen Kopf um 90° gegen den Uhrzeigersinn → Text lesbar
   - KEIN Text-Clipping (alle Buchstaben vollständig sichtbar)

4. **Vergleich mit Fehlern**
   - ❌ **FALSCH (alter Code)**: Text ist 180° gedreht (auf dem Kopf, kopfüber)
   - ❌ **FALSCH**: Text ist seitlich (270° oder -90°)
   - ❌ **FALSCH**: Text ist abgeschnitten (Clipping)
   - ✅ **RICHTIG**: Text ist 90° gedreht, von unten nach oben lesbar

### Visuelle Referenz

```
Toolbar (rechts, 110px breit)
┌─────┐
│  Z  │  ← "Zeiten" (von unten nach oben gelesen)
│  e  │
│  i  │
│  t  │
│  e  │
│  n  │
├─────┤
│  A  │  ← "Aufnahme"
│  u  │
│  f  │
│  n  │
│  a  │
│  h  │
│  m  │
│  e  │
└─────┘
```

### ✅ Erfolgskriterien
- [ ] Text ist 90° gedreht (vertikal)
- [ ] Text ist von unten nach oben lesbar (Kopf 90° gegen Uhrzeigersinn drehen)
- [ ] Kein Text-Clipping, alle Buchstaben sichtbar
- [ ] Buttons haben ausreichend Padding

### ❌ Fehlerbehandlung
- **Problem**: Text ist 180° gedreht (auf dem Kopf)
  - **Lösung**: Prüfe `VerticalButton._update_rotation()` - sollte `angle=90` verwenden (nicht 180)

- **Problem**: Text ist abgeschnitten
  - **Lösung**: Prüfe `VerticalButton.__init__()` - sollte `self.padding = [dp(10), dp(5)]` haben

---

## Test 4: 16:9-Modus (Regression Test)

### Ziel
Sicherstellen, dass 16:9-Modus weiterhin korrekt funktioniert.

### Schritte

1. **App im 16:9-Modus starten**
   - `python3 main.py`
   - Format → "Horizontal 16:9"

2. **Visuelle Inspektion**
   - Toolbar sollte **unten** sein (horizontal)
   - Button-Texte sollten **horizontal** sein (keine Rotation)
   - Bilder sollten im **oberen Bereich** angezeigt werden (ohne Toolbar-Höhe)

3. **Bildgenerierung testen**
   - Bild generieren im 16:9-Modus
   - Prüfen: Bild ist 1920x1080 (nicht 1080x1920)

4. **Debug-Logs prüfen**
   ```bash
   tail -30 "/home/pi/Desktop/v2_Tripple S/projekt.log" | grep -i "16:9 mode\|content="
   ```
   
   **Erwartete Log-Einträge:**
   ```
   [DEBUG] 16:9 mode: window=1920x1080, toolbar_height=60, content=1920x1020
   ```

### ✅ Erfolgskriterien
- [ ] Toolbar ist unten (horizontal)
- [ ] Button-Texte sind horizontal (keine Rotation)
- [ ] Bilder werden korrekt im oberen Bereich angezeigt
- [ ] Generierte Bilder sind 1920x1080

---

## Test 5: Doppelklick-Hänger (Galerie)

### Ziel
Verifizieren, dass Doppelklick auf Galerie-Bilder nicht mehr zum App-Freeze führt.

### Schritte

1. **Galerie öffnen**
   - `python3 main.py`
   - "Galerie"-Button klicken

2. **Einfacher Doppelklick**
   - Doppelklick auf ein Thumbnail-Bild
   - **Erwartet**: Lightbox öffnet sich sofort
   - **Erwartet**: App bleibt responsive

3. **Mehrfacher schneller Doppelklick (Stress-Test)**
   - Doppelklick auf Bild
   - Sofort nochmal doppelklicken (3-4x innerhalb von 1 Sekunde)
   - **Erwartet**: Nur eine Lightbox öffnet sich
   - **Erwartet**: App bleibt responsive, kein Freeze

4. **Lightbox schließen und wiederholen**
   - Lightbox mit "✕" schließen
   - Erneut doppelklicken
   - **Erwartet**: Lightbox öffnet sich wieder
   - **Erwartet**: Kein Memory-Leak, Performance bleibt gut

5. **Debug-Logs prüfen**
   ```bash
   tail -50 "/home/pi/Desktop/v2_Tripple S/projekt.log" | grep -i "lightbox"
   ```
   
   **Erwartete Log-Einträge:**
   ```
   [DEBUG] Scheduled lightbox open for: /path/to/image.png
   [INFO] Lightbox opened for: /path/to/image.png
   [DEBUG] Lightbox closed, flag reset for: /path/to/image.png
   [INFO] Lightbox closed for: /path/to/image.png
   ```

6. **Fehlerfall testen**
   - Doppelklick auf fehlerhaftes/nicht existierendes Bild
   - **Erwartet**: Fehlermeldung in Lightbox, kein Crash
   - **Erwartet**: Log zeigt Error-Nachricht

### ✅ Erfolgskriterien
- [ ] Einfacher Doppelklick öffnet Lightbox sofort
- [ ] Mehrfacher Doppelklick öffnet nur eine Lightbox
- [ ] App friert nicht ein
- [ ] Lightbox kann geschlossen und erneut geöffnet werden
- [ ] Fehlerhafte Bilder führen zu Fehlermeldung statt Crash
- [ ] Logs zeigen korrekte Debounce-Nachrichten

### ❌ Fehlerbehandlung
- **Problem**: App friert ein beim Doppelklick
  - **Lösung**: Prüfe ob `_open_lightbox_debounced()` implementiert ist
  - Prüfe ob `Clock.schedule_once` mit 0.25s verwendet wird

- **Problem**: Mehrere Lightboxes öffnen sich
  - **Lösung**: Prüfe ob `is_lightbox_open` Flag korrekt gesetzt/zurückgesetzt wird

---

## Test 6: Format-Wechsel (9:16 ↔ 16:9)

### Ziel
Sicherstellen, dass Format-Wechsel keine Layout-Probleme verursacht.

### Schritte

1. **Starte im 16:9-Modus mit geladenem Bild**
   - `python3 main.py`
   - Warte bis Slideshow ein Bild lädt

2. **Wechsel zu 9:16**
   - Format-Button → "Vertikal 9:16"
   - **Erwartet**: 
     - Layout wechselt sofort
     - Toolbar springt von unten nach rechts
     - Bild wird neu positioniert (zentriert im Content-Bereich)
     - Kein weißer Hintergrund erscheint

3. **Wechsel zurück zu 16:9**
   - Format-Button → "Horizontal 16:9"
   - **Erwartet**:
     - Layout wechselt sofort
     - Toolbar springt von rechts nach unten
     - Bild wird neu positioniert (zentriert im oberen Bereich)

4. **Mehrfacher schneller Wechsel**
   - Format mehrmals hintereinander wechseln (5x)
   - **Erwartet**: Keine Fehler, Layout immer korrekt

5. **Debug-Logs prüfen**
   ```bash
   tail -50 "/home/pi/Desktop/v2_Tripple S/projekt.log" | grep -i "applying layout\|aspect ratio"
   ```
   
   **Erwartete Log-Einträge:**
   ```
   [INFO] Applying layout for aspect ratio: 9:16, window size: 1920x1080
   [INFO] Created vertical toolbar for 9:16 mode
   [INFO] Applying layout for aspect ratio: 16:9, window size: 1920x1080
   [INFO] Created horizontal toolbar for 16:9 mode
   ```

### ✅ Erfolgskriterien
- [ ] Layout wechselt sofort ohne Verzögerung
- [ ] Toolbar springt zwischen rechts (9:16) und unten (16:9)
- [ ] Bilder werden korrekt neu positioniert
- [ ] Kein weißer Hintergrund beim Wechsel
- [ ] Mehrfacher Wechsel funktioniert ohne Fehler

---

## Zusammenfassung: Alle Tests bestanden?

### Checkliste
- [ ] Test 1: 9:16 Bildgenerierung → 1080x1920 (nicht 1920x1080)
- [ ] Test 2: 9:16 Bildanzeige → keine Weißflächen
- [ ] Test 3: 9:16 Menü → Text 90° gedreht, von unten nach oben lesbar
- [ ] Test 4: 16:9 Regression → Toolbar unten, Text horizontal
- [ ] Test 5: Doppelklick → kein Freeze, nur eine Lightbox
- [ ] Test 6: Format-Wechsel → Layout korrekt, keine Fehler

### Bei Problemen
1. Prüfe `projekt.log` auf Fehlermeldungen
2. Prüfe ob alle Dateien die neuesten Änderungen haben:
   - `PythonServer.py` (aspect-aware scaling)
   - `vertex_ai_image_workflow.py` (PIL logging suppression)
   - `main.py` (rotation fix, debounce, keep_ratio)
3. Prüfe `image_meta.json` Inhalt
4. Stelle sicher dass Kivy und PIL/Pillow installiert sind

### Log-Analyse-Befehle
```bash
# Alle aspect-ratio relevanten Einträge
grep -i "aspect" "/home/pi/Desktop/v2_Tripple S/projekt.log" | tail -20

# Alle Scaling-Einträge
grep -i "scaling\|scaled" "/home/pi/Desktop/v2_Tripple S/projekt.log" | tail -20

# Alle Layout-Einträge
grep -i "layout\|toolbar" "/home/pi/Desktop/v2_Tripple S/projekt.log" | tail -20

# Alle Lightbox-Einträge
grep -i "lightbox" "/home/pi/Desktop/v2_Tripple S/projekt.log" | tail -20
```

---

## Weiterführende Informationen

- **CHANGELOG.md**: Detaillierte Beschreibung aller Änderungen
- **FIX_SUMMARY.md**: Technische Zusammenfassung der Fixes
- **QUICK_START.md**: Schnellstart-Anleitung für Tests
- **projekt.log**: Laufzeit-Logs für Debugging

Bei Fragen oder Problemen, siehe die Log-Dateien oder erstelle ein Issue auf GitHub.
