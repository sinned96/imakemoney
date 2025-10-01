# Bildauswahl-Feature: Ablaufdiagramm

## Übersicht

Die erweiterte Bildauswahl ermöglicht Zugriff auf zwei verschiedene Bildquellen.

## Quellordner

```
Bildquellen:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Galerie (KI-Bilder)          Import (Uploads)                 │
│  ═══════════════════           ═══════════════                  │
│                                                                 │
│  BilderVertex/                 uploads/                        │
│  ├── bild_001.png              ├── import_20240115_photo1.jpg  │
│  ├── bild_002.png              ├── import_20240115_photo2.jpg  │
│  └── ...                       └── ...                         │
│                                                                 │
│  KI-generierte Bilder          Importierte Bilder              │
│                                (Mobile Upload/Aufnahme)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Benutzer-Workflow

### 1. Aufnahme-Funktion öffnen

```
Benutzer klickt:
  "📷 Bild hinzufügen (optional)"
       ↓
  AufnahmePopup.open_image_selection()
```

### 2. Tabbed Interface

```
┌─────────────────────────────────────────────────────────────┐
│  Bild für Aufnahme auswählen                          [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┬──────────────────────┐           │
│  │ Galerie (KI-Bilder) │ Import (Uploads)    │           │
│  └─────────────────────┬┴──────────────────────┘           │
│                        │                                    │
│  Aktiver Tab          │                                    │
│  ════════════          │                                    │
│                        │                                    │
│  ┌─────────────────────┼─────────────────────────────────┐ │
│  │                     │                                 │ │
│  │  📁 /home/pi/Desktop/v2_Tripple S/BilderVertex      │ │
│  │                     │                                 │ │
│  │  📄 bild_001.png    │                                 │ │
│  │  📄 bild_002.png    │                                 │ │
│  │  📄 bild_003.png    │                                 │ │
│  │                     │                                 │ │
│  └─────────────────────┼─────────────────────────────────┘ │
│                        │                                    │
│  ┌────────────┐ ┌──────┴────────┐                          │
│  │ Auswählen  │ │  Abbrechen   │                          │
│  └────────────┘ └───────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Tab-Wechsel

```
Benutzer klickt auf: "Import (Uploads)"
       ↓
┌─────────────────────────────────────────────────────────────┐
│  Bild für Aufnahme auswählen                          [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┬──────────────────────┐           │
│  │ Galerie (KI-Bilder) │ Import (Uploads)    │           │
│  └──────────────────────┴─────────────────────┬┘           │
│                                               │            │
│                        Aktiver Tab            │            │
│                        ════════════            │            │
│                                               │            │
│  ┌────────────────────────────────────────────┼──────────┐ │
│  │                                            │          │ │
│  │  📁 /home/pi/Desktop/v2_Tripple S/uploads │          │ │
│  │                                            │          │ │
│  │  📄 import_20240115_123456_photo1.jpg     │          │ │
│  │  📄 import_20240115_123457_photo2.jpg     │          │ │
│  │                                            │          │ │
│  └────────────────────────────────────────────┼──────────┘ │
│                                               │            │
│  ┌────────────┐ ┌──────────────┐             │            │
│  │ Auswählen  │ │  Abbrechen  │             │            │
│  └────────────┘ └──────────────┘             │            │
│                                               │            │
└─────────────────────────────────────────────────────────────┘
```

### 4. Bildauswahl

```
Benutzer wählt Bild und klickt "Auswählen"
       ↓
  process_selected_image()
       ↓
  Bild wird für Aufnahme vorbereitet
       ↓
  ✓ "Bild ausgewählt: photo1.jpg"
```

## Technische Implementation

### Code-Flow

```python
def open_image_selection(self, instance):
    # 1. Create TabbedPanel
    tab_panel = TabbedPanel(do_default_tab=False)
    
    # 2. Gallery Tab
    gallery_tab = TabbedPanelItem(text='Galerie (KI-Bilder)')
    gallery_chooser = FileChooserListView(path=IMAGE_DIR)
    gallery_tab.add_widget(gallery_chooser)
    
    # 3. Import Tab
    import_tab = TabbedPanelItem(text='Import (Uploads)')
    import_chooser = FileChooserListView(path=IMPORT_DIR)
    import_tab.add_widget(import_chooser)
    
    # 4. Selection Logic
    def select_file():
        if tab_panel.current_tab == gallery_tab:
            active_chooser = gallery_chooser
        else:
            active_chooser = import_chooser
        
        if active_chooser.selection:
            self.process_selected_image(active_chooser.selection[0])
```

## Vorteile

1. ✅ **Klare Trennung**: KI-Bilder und Import-Bilder getrennt
2. ✅ **Einfache Navigation**: Tab-basierte Auswahl
3. ✅ **Konsistente UX**: Gleiche Funktionalität für beide Quellen
4. ✅ **Flexible Erweiterung**: Weitere Tabs können hinzugefügt werden

## Verzeichnisstruktur

```
/home/pi/Desktop/v2_Tripple S/
├── BilderVertex/          # Galerie-Quelle (Tab 1)
│   ├── bild_001.png
│   ├── bild_002.png
│   └── ...
│
├── uploads/               # Import-Quelle (Tab 2)
│   ├── import_20240115_123456_photo1.jpg
│   ├── import_20240115_123457_photo2.jpg
│   └── ...
│
├── transkript.json
└── projekt.log
```

## Modi-Integration

Die Galerie-Anzeige nutzt ebenfalls die gleichen Ordner:

```
Modi-Liste:
├── Tag         → lädt aus BilderVertex
├── Nacht       → lädt aus BilderVertex  
├── Urlaub      → lädt aus BilderVertex
└── Import      → lädt aus uploads ✓
```

## Hinweise

- **Bildauswahl**: Funktioniert auch wenn Ordner nicht existiert (Fallback: Home)
- **Doppelklick**: Funktioniert für beide Quellen identisch
- **Mobile Upload**: Speichert automatisch in uploads-Ordner
