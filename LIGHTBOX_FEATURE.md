# Lightbox Feature - Bildanzeige in der Galerie

## Überblick

Die Galerie-Ansicht in der Anwendung unterstützt jetzt die Anzeige von Bildern in einer Lightbox/Overlay-Ansicht durch Doppelklick oder Doppeltipp.

## Funktionsweise

### Desktop (Maus)
1. Öffnen Sie die Galerie-Ansicht in der Anwendung
2. Doppelklicken Sie auf ein beliebiges Bild-Thumbnail
3. Das Bild wird in voller Größe und zentriert angezeigt

### Touch-Geräte
1. Öffnen Sie die Galerie-Ansicht in der Anwendung
2. Tippen Sie zweimal schnell hintereinander auf ein Bild-Thumbnail
3. Das Bild wird in voller Größe und zentriert angezeigt

## Lightbox-Funktionen

### Darstellung
- **Dunkler Hintergrund**: 90% Opazität für optimalen Fokus auf das Bild
- **Zentrierte Anzeige**: Bild wird mittig auf dem Bildschirm positioniert
- **Seitenverhältnis**: Das ursprüngliche Seitenverhältnis des Bildes bleibt erhalten
- **Responsive Größe**: Nutzt 90% der Bildschirmgröße (Breite und Höhe)
- **Dateiname**: Anzeige des Dateinamens am unteren Rand

### Schließen der Lightbox
Es gibt drei Möglichkeiten, die Lightbox zu schließen:

1. **Schließen-Button**: Klicken/Tippen auf das ✕ Symbol oben rechts
2. **Hintergrund-Klick**: Klicken/Tippen auf den dunklen Hintergrund (außerhalb des Bildes)
3. **ESC-Taste**: (Bei zukünftigen Erweiterungen geplant)

## Technische Details

### ImageLightboxPopup Klasse
Die neue `ImageLightboxPopup` Klasse wurde implementiert mit folgenden Features:
- Vollbildüberlagerung mit dunklem Hintergrund
- Dynamische Größenanpassung bei Fenstergrößenänderung
- Sauberes Cleanup beim Schließen (Event-Handler werden entfernt)
- Touch-Event-Handling für intuitive Bedienung

### ImageTile Doppelklick-Erkennung
Die `ImageTile` Klasse wurde erweitert um:
- Zeitbasierte Doppelklick-/Doppeltipp-Erkennung (0.3 Sekunden Schwellenwert)
- Unterscheidung zwischen Bildbereich und Schaltflächen
- Verhinderung von Dreifach-Klick-Problemen
- Kompatibilität mit Maus- und Touch-Eingaben

## Nutzungshinweise

### Best Practices
- Doppelklicken Sie direkt auf das Bild, nicht auf die Schaltflächen darunter
- Bei Touch-Geräten: Tippen Sie zweimal schnell hintereinander (innerhalb von 0.3 Sekunden)
- Die Lightbox passt sich automatisch an die Bildschirmgröße an

### Bekannte Einschränkungen
- Die Lightbox öffnet sich nur über Doppelklick/-tipp auf den Bildbereich
- Einfacher Klick auf das Bild hat keine Wirkung (normales Verhalten bleibt erhalten)
- Die Schaltflächen "Auswählen" und "⚙" behalten ihre normale Funktionalität

## Implementierungsdetails

### Dateien geändert
- `main.py`: Hinzufügung der `ImageLightboxPopup` Klasse und Erweiterung der `ImageTile` Klasse

### Code-Änderungen
- **Neue Klasse**: `ImageLightboxPopup` (ca. 80 Zeilen)
- **Erweiterte Funktionen in ImageTile**:
  - `on_touch_down()`: Doppelklick-Erkennung
  - `_open_lightbox()`: Lightbox-Öffnung
  - Neue Attribute: `last_touch_time`, `double_click_threshold`

### Kompatibilität
- Funktioniert mit Kivy Framework
- Kompatibel mit allen bestehenden Funktionen der Galerie
- Keine Änderungen an bestehenden APIs oder Datenstrukturen

## Zukünftige Erweiterungen

Mögliche zukünftige Verbesserungen könnten sein:
- Zoom-Funktionalität innerhalb der Lightbox
- Navigation zwischen Bildern (Vor/Zurück)
- Tastaturkürzel (ESC zum Schließen, Pfeiltasten zum Navigieren)
- Animationen beim Öffnen/Schließen
- Bildrotation innerhalb der Lightbox
- Teilen-Funktion direkt aus der Lightbox

## Support

Bei Fragen oder Problemen mit der Lightbox-Funktionalität:
1. Überprüfen Sie, ob Sie auf das Bild selbst doppelklicken
2. Stellen Sie sicher, dass die Zeitspanne zwischen den Klicks/Tipps < 0.3 Sekunden beträgt
3. Überprüfen Sie die Logs für eventuelle Fehler
