# Lightbox Feature - Workflow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      Galerie-Ansicht                             │
│                                                                  │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐                │
│  │ Bild 1 │  │ Bild 2 │  │ Bild 3 │  │ Bild 4 │                │
│  │ [Img]  │  │ [Img]  │  │ [Img]  │  │ [Img]  │                │
│  │ Name   │  │ Name   │  │ Name   │  │ Name   │                │
│  │[Select]│  │[Select]│  │[Select]│  │[Select]│                │
│  └────────┘  └────────┘  └────────┘  └────────┘                │
│      ▲                                                           │
│      │                                                           │
│      │ Doppelklick / Doppeltipp auf Bild                        │
│      │                                                           │
└──────┼───────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Lightbox-Overlay                              │
│  ┌────────────────────────────────────────────────────┐   ┌──┐  │
│  │                                                    │   │✕ │  │
│  │                                                    │   └──┘  │
│  │                                                    │         │
│  │                                                    │         │
│  │                                                    │         │
│  │              ┌──────────────────┐                 │         │
│  │              │                  │                 │         │
│  │              │                  │                 │         │
│  │              │   BILD GROSS     │                 │         │
│  │              │   (90% Größe)    │                 │         │
│  │              │                  │                 │         │
│  │              │                  │                 │         │
│  │              └──────────────────┘                 │         │
│  │                                                    │         │
│  │                                                    │         │
│  │                                                    │         │
│  │              [ Bildname.jpg ]                      │         │
│  │                                                    │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                  │
│  Dunkler Hintergrund (90% Opazität)                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
       │
       │ Schließen durch:
       │ - Klick auf ✕ Button
       │ - Klick auf dunklen Hintergrund
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│              Zurück zur Galerie-Ansicht                          │
└──────────────────────────────────────────────────────────────────┘
```

## Komponenten-Interaktion

### 1. ImageTile (Thumbnail in Galerie)
```
┌─────────────────────────┐
│  ImageTile              │
│  ┌─────────────────┐    │
│  │  Image Widget   │◄───┼─── on_touch_down() erkennt Doppelklick
│  └─────────────────┘    │
│  [ Bildname ]           │
│  [Select] [⚙]          │
└─────────────────────────┘
         │
         │ Bei Doppelklick
         ▼
    _open_lightbox()
         │
         ▼
    Findet Root-Widget
         │
         ▼
    Fügt ImageLightboxPopup hinzu
```

### 2. ImageLightboxPopup (Vollbild-Overlay)
```
┌────────────────────────────────────┐
│  ImageLightboxPopup                │
│  ┌──────────────────────────────┐  │
│  │  FloatLayout (Container)     │  │
│  │  ┌────────────────────────┐  │  │
│  │  │  Image (90% Größe)     │  │  │◄── allow_stretch=True
│  │  │  keep_ratio=True       │  │  │    keep_ratio=True
│  │  └────────────────────────┘  │  │
│  │  [ Close Button ]            │  │
│  │  [ Filename Label ]          │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Dark Background (90%)       │  │◄── on_touch_down() Handler
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

## Event-Flow

### Desktop (Maus)
```
1. Maus über ImageTile
2. Klick 1 → Zeit gespeichert in last_touch_time
3. Klick 2 innerhalb 0.3s → Doppelklick erkannt
4. _open_lightbox() aufgerufen
5. ImageLightboxPopup erstellt und zur Root hinzugefügt
6. Lightbox zeigt Bild an
7. Klick auf ✕ oder Hintergrund → _close()
8. ImageLightboxPopup entfernt
9. Zurück zur Galerie
```

### Touch (Mobil/Tablet)
```
1. Touch auf ImageTile
2. Tap 1 → Zeit gespeichert in last_touch_time
3. Tap 2 innerhalb 0.3s → Doppeltipp erkannt
4. _open_lightbox() aufgerufen
5. ImageLightboxPopup erstellt und zur Root hinzugefügt
6. Lightbox zeigt Bild an
7. Touch auf Hintergrund → _close()
8. ImageLightboxPopup entfernt
9. Zurück zur Galerie
```

## Wichtige Schwellenwerte

- **Doppelklick-Zeitfenster**: 0.3 Sekunden (double_click_threshold)
- **Bildgröße in Lightbox**: 90% der Fensterbreite und -höhe
- **Hintergrund-Opazität**: 90% (0.9)

## Fehlerbehandlung

### Szenarien die verhindert werden:
1. **Triple-Click**: Timer wird nach Doppelklick zurückgesetzt
2. **Button-Konflikt**: Nur Bild-Bereich löst Lightbox aus, nicht Buttons
3. **Memory Leaks**: Window-Events werden beim Schließen entfernt
4. **Mehrfach-Öffnung**: Jede Lightbox-Instanz ist unabhängig

### Edge Cases die behandelt werden:
1. Sehr große Bilder: Automatische Skalierung auf 90% der Fenstergröße
2. Sehr kleine Bilder: Skalierung mit Seitenverhältnis-Erhaltung
3. Fenstergrößenänderung: Dynamische Anpassung der Bildgröße
4. Verschiedene Seitenverhältnisse: keep_ratio=True erhält Proportionen
