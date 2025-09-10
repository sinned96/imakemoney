# Getrennte Workflow-Implementierung (Variante 3)

Diese Dokumentation beschreibt die Implementation der getrennten Workflow-Architektur für das imakemoney-Projekt.

## Übersicht

Das System wurde entsprechend der Anforderungen in zwei unabhängige Komponenten aufgeteilt:

1. **GUI (main.py)** - Startet und stoppt nur Aufnahme.py
2. **Workflow-Manager (PythonServer.py)** - Läuft im Hintergrund und verarbeitet Trigger

## Architektur

```
GUI (main.py)                    Workflow-Manager (PythonServer.py)
     |                                        |
     v                                        |
[Aufnahme starten/stoppen]                   |
     |                                        |
     v                                        |
[workflow_trigger.txt]          ------>  [FileWatcher]
     |                                        |
     v                                        v
[workflow_status.log]           <------  [Workflow ausführen]
     |
     v
[Status anzeigen]
```

## Datei-basierte Kommunikation

### Trigger-Datei: `workflow_trigger.txt`
- **Zweck**: Signalisiert dem Workflow-Manager, dass die Aufnahme beendet ist
- **Inhalt**: `"run"`
- **Erstellt von**: GUI (main.py) nach Stoppen der Aufnahme
- **Verarbeitet von**: Workflow-Manager (PythonServer.py)
- **Gelöscht von**: Workflow-Manager nach Abschluss

### Status-Log: `workflow_status.log`
- **Zweck**: Übermittelt Status-Updates vom Workflow-Manager zur GUI
- **Format**: `[TIMESTAMP] LEVEL: MESSAGE`
- **Geschrieben von**: Workflow-Manager
- **Gelesen von**: GUI (zeigt Status in der AufnahmePopup an)

## Komponenten im Detail

### 1. GUI-Komponente (main.py)

#### Neue Funktionen in AufnahmePopup:

```python
def create_workflow_trigger(self):
    """Erstellt Trigger-Datei nach Aufnahme-Stopp"""
    
def check_workflow_status(self, dt):
    """Liest und zeigt Workflow-Status aus Log-Datei"""
```

#### Ablauf:
1. Benutzer startet Aufnahme → `Aufnahme.py` wird als Subprocess gestartet
2. Benutzer stoppt Aufnahme → `Aufnahme.py` wird mit SIGTERM beendet
3. GUI erstellt `workflow_trigger.txt` mit Inhalt `"run"`
4. GUI startet Timer um `workflow_status.log` zu überwachen
5. GUI zeigt Status-Updates aus Log-Datei an
6. GUI stoppt Überwachung bei `WORKFLOW_COMPLETE` oder `WORKFLOW_ERROR`

### 2. Workflow-Manager (PythonServer.py)

#### Neue Klasse: WorkflowFileWatcher

```python
class WorkflowFileWatcher:
    def start_watching(self):     # Startet Hintergrund-Thread
    def check_trigger(self):      # Prüft auf Trigger-Datei  
    def execute_workflow(self):   # Führt Workflow aus
    def log_status(self):         # Schreibt Status-Updates
```

#### Ablauf:
1. Läuft als Hintergrunddienst
2. Überwacht `workflow_trigger.txt` jede Sekunde
3. Bei Trigger-Erkennung:
   - Führt `voiceToGoogle.py` aus (Spracherkennung)
   - Führt `dateiKopieren.py` aus (Dateiverwaltung)
   - Führt Bildgenerierung aus
   - Loggt jeden Schritt in `workflow_status.log`
   - Löscht `workflow_trigger.txt`
   - Schreibt `WORKFLOW_COMPLETE` oder `WORKFLOW_ERROR`

## Verwendung

### Workflow-Manager als Service starten

```bash
# Direkt starten
python3 PythonServer.py --service

# Mit Starter-Script
python3 start_workflow_service.py
```

### GUI verwenden

```bash
# GUI starten (wie gewohnt)
python3 main.py
```

1. GUI öffnet sich mit Login-Bildschirm
2. Nach Login: Slideshow mit Aufnahme-Button
3. Klick auf "Aufnahme" → AufnahmePopup öffnet sich
4. "Start" → Aufnahme beginnt
5. "Stopp" → Aufnahme endet, Workflow wird automatisch getriggert
6. Status-Updates erscheinen in der Popup-Ausgabe

## Robustheit & Fehlerbehandlung

### Umgebungserkennung
- **Raspberry Pi**: Automatisch erkannt über `/etc/rpi-issue`
- **Headless**: Clipboard-Operationen werden graceful behandelt
- **Desktop**: Vollständige Funktionalität

### Fehlerbehandlung
- **Fehlende Dependencies**: Graceful Fallbacks (z.B. Demo-Bildgenerierung)
- **Prozess-Fehler**: Vollständige stdout/stderr-Sammlung
- **Datei-Konflikte**: Atomare Operationen, Retry-Mechanismen
- **Signal-Behandlung**: Saubere SIGTERM-Behandlung

### Logging-Levels
- **INFO**: Normale Workflow-Schritte
- **WARNING**: Nicht-kritische Fehler (Workflow läuft weiter)
- **ERROR**: Kritische Fehler (Workflow stoppt)

## Test & Verifikation

### Automatische Tests ausführen
```bash
python3 test_separated_workflow.py
```

Tests prüfen:
- ✅ Trigger-Datei Mechanismus
- ✅ Status-Logging
- ✅ Hintergrund-Watcher
- ✅ GUI-Integration

### Manuelle Tests

1. **Service-Test**:
   ```bash
   python3 PythonServer.py --service &
   echo "run" > workflow_trigger.txt
   # → Workflow sollte automatisch starten
   ```

2. **GUI-Test**:
   ```bash
   python3 main.py
   # → Login → Aufnahme → Start/Stopp
   # → Status sollte in GUI erscheinen
   ```

## Dateien

### Modifiziert
- **main.py**: AufnahmePopup erweitert um Trigger-Erstellung und Status-Anzeige
- **PythonServer.py**: WorkflowFileWatcher-Klasse hinzugefügt

### Neu erstellt
- **start_workflow_service.py**: Utility zum Starten des Services
- **test_separated_workflow.py**: Umfassende Tests
- **SEPARATED_WORKFLOW.md**: Diese Dokumentation

### Laufzeit-Dateien
- **workflow_trigger.txt**: Temporäre Trigger-Datei
- **workflow_status.log**: Status-Log (persistent)

## Kompatibilität

### Betriebssysteme
- ✅ **Raspberry Pi OS**: Vollständig getestet
- ✅ **Ubuntu/Debian**: Vollständig getestet  
- ✅ **Windows**: Grundfunktionen (Signal-Behandlung limitiert)
- ✅ **macOS**: Grundfunktionen

### Python-Versionen
- ✅ **Python 3.8+**: Empfohlen
- ✅ **Python 3.7**: Unterstützt mit Einschränkungen

### Dependencies
- **Erforderlich**: `pyperclip`, `requests`
- **Optional**: `google-cloud-aiplatform` (für echte Bildgenerierung)
- **GUI**: `kivy`, `kivymd` (nur für main.py)

## Erweitungen & Anpassungen

### Neue Workflow-Schritte hinzufügen

1. Script in `WorkflowFileWatcher.execute_workflow()` hinzufügen:
   ```python
   self.log_status("Neuer Schritt...")
   success = manager.run_script_sync("new_script.py", "Beschreibung")
   ```

2. Entsprechende Logging-Nachrichten anpassen

### Trigger-Mechanismus erweitern

Weitere Trigger-Typen über Datei-Inhalt:
```python
# workflow_trigger.txt Inhalte:
"run"           # Standard-Workflow
"run_fast"      # Schneller Workflow (weniger Schritte)
"run_custom"    # Benutzerdefinierter Workflow
```

### GUI Status-Anzeige anpassen

In `main.py` `check_workflow_status()` modifizieren für:
- Fortschrittsbalken
- Detailliertere Status-Anzeige
- Benutzerdefinierte Aktionen bei Completion

## Troubleshooting

### Workflow startet nicht
1. Prüfen: `python3 PythonServer.py --service` läuft
2. Prüfen: `workflow_trigger.txt` wird erstellt
3. Prüfen: Berechtigungen im Arbeitsverzeichnis

### Status wird nicht angezeigt
1. Prüfen: `workflow_status.log` wird erstellt
2. Prüfen: GUI-Timer läuft (`Clock.schedule_interval`)
3. Prüfen: Datei-Berechtigungen

### Aufnahme funktioniert nicht
1. Prüfen: `arecord` oder `parecord` installiert
2. Prüfen: Audio-Hardware verfügbar
3. Prüfen: Berechtigungen für Audio-Zugriff

Die Implementation erfüllt alle Anforderungen der Variante 3 und bietet eine robuste, testbare Lösung für die getrennte Workflow-Architektur.