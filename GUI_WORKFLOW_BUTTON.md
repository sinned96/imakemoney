# GUI Workflow Service Button - Benutzerhandbuch

Diese Dokumentation beschreibt die neue "Workflow starten" Button-Funktionalität in der GUI.

## Übersicht

Die GUI (`main.py`) verfügt jetzt über einen integrierten Button zum Starten und Stoppen des Workflow-Services (`PythonServer.py`). Damit kann der Hintergrund-Service direkt aus der GUI heraus verwaltet werden, ohne separate Terminal-Befehle zu benötigen.

## Funktionsweise

### 1. Button-Location
Der "Workflow starten" Button befindet sich in der Toolbar der GUI:
- **KivyMD Version**: Play/Stop-Icon in der rechten Toolbar
- **Standard Version**: Text-Button "Workflow starten" / "Service Stopp"

### 2. Button-Verhalten

#### Wenn kein Service läuft:
- **Button zeigt**: "Workflow starten" ▶️ 
- **Klick-Aktion**: Startet `PythonServer.py --service` als Hintergrundprozess
- **Nach Start**: Button ändert sich zu "Service Stopp" 🛑

#### Wenn Service läuft:
- **Button zeigt**: "Service Stopp" 🛑
- **Klick-Aktion**: Stoppt den Service sauber mit SIGTERM
- **Nach Stopp**: Button ändert sich zu "Workflow starten" ▶️

### 3. Automatische Status-Erkennung
- Die GUI prüft alle 10 Sekunden den Service-Status
- Button-Text und -Icon werden automatisch aktualisiert
- Service-Erkennung über Prozess-Status und Log-Datei-Aktivität

## Verwendung

### Schritt 1: GUI starten
```bash
python3 main.py
```

### Schritt 2: Login
- Anmeldung mit Benutzerdaten
- GUI zeigt Slideshow mit Toolbar

### Schritt 3: Workflow-Service starten
- Klick auf "Workflow starten" Button in der Toolbar
- Service startet automatisch im Hintergrund
- Button zeigt jetzt "Service Stopp"

### Schritt 4: Aufnahme-Workflow verwenden
1. **Aufnahme starten**: Klick auf "Aufnahme" Button
2. **Aufnahme durchführen**: Start/Stop in der Aufnahme-Popup
3. **Automatische Verarbeitung**: Service verarbeitet automatisch:
   - Spracherkennung (`voiceToGoogle.py`)
   - Dateiverwaltung (`dateiKopieren.py`) 
   - Bildgenerierung (KI-basiert)
4. **Status-Updates**: Werden in der Aufnahme-Popup angezeigt

### Schritt 5: Service stoppen (optional)
- Klick auf "Service Stopp" Button
- Service wird sauber beendet
- Button zeigt wieder "Workflow starten"

## Technische Details

### Service-Management
- **Start**: `subprocess.Popen` mit Prozessgruppen
- **Stop**: SIGTERM für sauberes Herunterfahren, SIGKILL als Fallback
- **Überwachung**: Prozess-Polling und Log-Datei-Aktivität
- **Cleanup**: Automatische Bereinigung bei GUI-Exit

### Kommunikation
- **Trigger-Dateien**: `workflow_trigger.txt` (GUI → Service)
- **Status-Logs**: `workflow_status.log` (Service → GUI)
- **Prozess-IDs**: Direkte Prozess-Verwaltung für Start/Stop

### Cross-Platform Support
- ✅ **Raspberry Pi**: Vollständig getestet
- ✅ **Desktop Linux**: Vollständig getestet
- ✅ **Windows**: Grundfunktionen (Signal-Handling limitiert)
- ✅ **macOS**: Grundfunktionen

## Fehlerbehebung

### Service startet nicht
1. **Prüfen**: `PythonServer.py` ist im gleichen Verzeichnis
2. **Prüfen**: Python-Dependencies installiert (`pyperclip`, `requests`)
3. **Log-Ausgabe**: Terminal-Output der GUI für Fehlermeldungen

### Button zeigt falschen Status
1. **Warten**: Automatische Aktualisierung erfolgt alle 10 Sekunden
2. **Neustart**: GUI beenden und neu starten
3. **Manuell prüfen**: `ps aux | grep PythonServer` im Terminal

### Workflow funktioniert nicht
1. **Service-Status**: Prüfen ob "Service Stopp" angezeigt wird
2. **Log-Datei**: `workflow_status.log` auf Fehlermeldungen prüfen
3. **Berechtigungen**: Schreibzugriff auf Arbeitsverzeichnis prüfen

## Vorteile der Integration

### Benutzerfreundlichkeit
- ✅ Ein-Klick-Start des kompletten Workflow-Services
- ✅ Keine separaten Terminal-Befehle nötig
- ✅ Visueller Status-Indikator
- ✅ Automatische Button-Aktualisierung

### Robustheit
- ✅ Saubere Prozess-Verwaltung
- ✅ Automatische Service-Erkennung
- ✅ Graceful Shutdown mit Fallback
- ✅ Resource-Cleanup bei Exit

### Workflow-Integration
- ✅ Nahtlose Integration mit Aufnahme-Funktionalität
- ✅ Automatische Trigger-Verarbeitung
- ✅ Real-time Status-Updates
- ✅ Kompletter End-to-End Workflow

## Kompatibilität

### Bestehende Funktionen
- ✅ **Aufnahme-Popup**: Funktioniert unverändert
- ✅ **Trigger-Dateien**: Weiterhin vollständig unterstützt
- ✅ **Status-Logs**: Weiterhin lesbar und anzeigbar
- ✅ **Bildergalerie**: Neue Bilder erscheinen automatisch

### Legacy-Modi
- ✅ **Manueller Service-Start**: `python3 PythonServer.py --service`
- ✅ **Direkter Workflow**: `python3 PythonServer.py`
- ✅ **Original Workflow**: `python3 PythonServer.py --original`

---

**Diese Implementierung erfüllt alle Anforderungen der ursprünglichen Problemstellung und bietet eine robuste, benutzerfreundliche Lösung für die Workflow-Service-Verwaltung direkt aus der GUI.**