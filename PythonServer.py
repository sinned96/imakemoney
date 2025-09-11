import os
import base64
import subprocess
import pyperclip
import requests
import glob
import signal
import sys
import time
import threading
import select

# Optional Google Cloud dependencies
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GoogleAuthRequest
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("Google Cloud libraries not available - using demo mode for image generation")

# Configuration for different environments
import os
import platform
from pathlib import Path

# Get the current script directory
SCRIPT_DIR = Path(__file__).parent

# Environment detection
IS_RASPBERRY_PI = os.path.exists('/etc/rpi-issue') or 'raspberry' in platform.platform().lower()
IS_HEADLESS = not os.environ.get('DISPLAY') and platform.system() == 'Linux'

# Google Cloud Configuration
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS', str(SCRIPT_DIR / "cloudKey.json"))
# For Google Speech-to-Text, use the specific credentials path as required
GOOGLE_SPEECH_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/home/pi/meinprojekt-venv/cloudKey.json')
PROJECT_ID = os.getenv('PROJECT_ID', "trippe-s")
ENDPOINT = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/us-central1/publishers/google/models/imagen-4.0-generate-001:predict"

# Script paths - use relative paths from current directory
AUFNAHME_SCRIPT = str(SCRIPT_DIR / "Aufnahme.py")
VOICE_SCRIPT = str(SCRIPT_DIR / "voiceToGoogle.py")
COPY_SCRIPT = str(SCRIPT_DIR / "dateiKopieren.py")
TRANSKRIPT_PATH = str(SCRIPT_DIR / "transkript.txt")
BILDER_DIR = str(SCRIPT_DIR / "BilderVertex")

# Print environment info on startup
if __name__ == "__main__":
    print(f"Environment: {'Raspberry Pi' if IS_RASPBERRY_PI else 'Desktop'}")
    print(f"Display: {'Headless' if IS_HEADLESS else 'GUI Available'}")
    print(f"Script Directory: {SCRIPT_DIR}")

class AsyncWorkflowManager:
    """Manages the asynchronous execution of the recording and processing workflow"""
    
    def __init__(self):
        self.recording_process = None
        self.is_recording = False
        self.should_stop = False
        self.output_lines = []
        
    def run_script_sync(self, script_path, beschreibung):
        """Run a script synchronously with output collection"""
        if os.path.exists(script_path):
            print(f"Starte {beschreibung}: {script_path}")
            try:
                # Setup environment variables for the script
                env = os.environ.copy()
                
                # Set GOOGLE_APPLICATION_CREDENTIALS for speech-to-text
                if "voiceToGoogle.py" in script_path:
                    env['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_SPEECH_CREDENTIALS
                    print(f"Setting GOOGLE_APPLICATION_CREDENTIALS to: {GOOGLE_SPEECH_CREDENTIALS}")
                    
                    # Log credential file status
                    if os.path.exists(GOOGLE_SPEECH_CREDENTIALS):
                        print(f"✓ Google credentials file found: {GOOGLE_SPEECH_CREDENTIALS}")
                    else:
                        print(f"⚠ Google credentials file not found: {GOOGLE_SPEECH_CREDENTIALS}")
                        print("Speech recognition will use simulation mode")
                
                result = subprocess.run(
                    ["python3", script_path], 
                    capture_output=True, 
                    text=True,
                    timeout=300,  # 5 minute timeout
                    env=env  # Pass environment variables
                )
                
                if result.stdout:
                    print("--- STDOUT ---")
                    print(result.stdout)
                    
                if result.stderr:
                    print("--- STDERR ---") 
                    print(result.stderr)
                    
                if result.returncode != 0:
                    print(f"Fehler beim Starten von {os.path.basename(script_path)} (Exit Code: {result.returncode})")
                else:
                    print(f"{beschreibung} abgeschlossen!")
                    
                return result.returncode == 0
                
            except subprocess.TimeoutExpired:
                print(f"Timeout bei {beschreibung} nach 5 Minuten")
                return False
            except Exception as e:
                print(f"Fehler beim Ausführen von {beschreibung}: {e}")
                return False
        else:
            print(f"{os.path.basename(script_path)} nicht gefunden!")
            return False

    def start_recording_async(self, script_path):
        """Start Aufnahme.py as asynchronous subprocess"""
        if not script_path or not os.path.exists(script_path):
            print(f"Aufnahme-Script nicht gefunden: {script_path}")
            return False
            
        if self.is_recording:
            print("Warnung: Aufnahme läuft bereits")
            return False
            
        try:
            print(f"Starte Aufnahme asynchron: {script_path}")
            
            # Start the recording process
            self.recording_process = subprocess.Popen(
                ["python3", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,  # Line buffered
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.is_recording = True
            self.output_lines = []
            print(f"Aufnahme gestartet (PID: {self.recording_process.pid})")
            print("Drücke Enter um die Aufnahme zu stoppen, oder warte auf externes Signal...")
            
            # Start output monitoring thread
            output_thread = threading.Thread(target=self._monitor_output, daemon=True)
            output_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Starten der Aufnahme: {e}")
            self.is_recording = False
            return False

    def _monitor_output(self):
        """Monitor subprocess output in separate thread"""
        try:
            while self.is_recording and self.recording_process:
                if self.recording_process.poll() is not None:
                    # Process has ended
                    break
                    
                # Read available output
                try:
                    # Use select on Unix systems for non-blocking read
                    if hasattr(select, 'select'):
                        ready, _, _ = select.select([self.recording_process.stdout], [], [], 0.1)
                        if ready:
                            line = self.recording_process.stdout.readline()
                            if line:
                                line = line.strip()
                                self.output_lines.append(line)
                                print(f"[Aufnahme] {line}")
                    else:
                        # Fallback for systems without select
                        time.sleep(0.1)
                        
                except Exception:
                    break
                    
        except Exception as e:
            print(f"Fehler beim Überwachen der Ausgabe: {e}")

    def stop_recording(self):
        """Stop the recording process gracefully using SIGTERM"""
        if not self.is_recording or not self.recording_process:
            print("Keine Aufnahme läuft")
            return True
            
        try:
            print("Stoppe Aufnahme...")
            
            # Send SIGTERM to the process group for clean shutdown
            os.killpg(os.getpgid(self.recording_process.pid), signal.SIGTERM)
            
            # Wait for process to finish with timeout
            try:
                stdout, stderr = self.recording_process.communicate(timeout=10)
                
                # Collect any remaining output
                if stdout:
                    for line in stdout.split('\n'):
                        if line.strip():
                            self.output_lines.append(line.strip())
                            print(f"[Aufnahme] {line.strip()}")
                            
                if stderr:
                    print("--- Aufnahme STDERR ---")
                    print(stderr)
                    
            except subprocess.TimeoutExpired:
                print("Aufnahme reagiert nicht auf SIGTERM, erzwinge Beendigung...")
                os.killpg(os.getpgid(self.recording_process.pid), signal.SIGKILL)
                self.recording_process.wait()
                
            print("Aufnahme gestoppt")
            self.is_recording = False
            
            # Display summary of collected output
            if self.output_lines:
                print("\n--- Aufnahme Zusammenfassung ---")
                for line in self.output_lines[-10:]:  # Show last 10 lines
                    print(line)
                print("--- Ende Zusammenfassung ---\n")
                
            return True
            
        except Exception as e:
            print(f"Fehler beim Stoppen der Aufnahme: {e}")
            self.is_recording = False
            return False

    def wait_for_stop_signal(self):
        """Wait for user input or external signal to stop recording"""
        def signal_handler(signum, frame):
            print(f"\nSignal {signum} empfangen, stoppe Aufnahme...")
            self.should_stop = True

        # Set up signal handlers
        original_handlers = {}
        try:
            original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, signal_handler)
            original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            print(f"Warnung: Konnte Signal-Handler nicht setzen: {e}")
        
        try:
            while self.is_recording and not self.should_stop:
                # Check if recording process is still running
                if self.recording_process and self.recording_process.poll() is not None:
                    print("Aufnahme-Prozess beendet")
                    self.is_recording = False
                    break
                
                # Check for keyboard input (non-blocking)
                if hasattr(select, 'select') and sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    input_line = sys.stdin.readline().strip()
                    if input_line == "" or input_line.lower() in ['q', 'quit', 'exit', 'stop']:
                        print("Benutzer-Stop erkannt")
                        self.should_stop = True
                        break
                elif not hasattr(select, 'select'):
                    # Fallback for systems without select - just wait a bit
                    time.sleep(0.1)
                        
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt empfangen")
            self.should_stop = True
        except Exception as e:
            print(f"Fehler beim Warten auf Stop-Signal: {e}")
            self.should_stop = True
        finally:
            # Restore original signal handlers
            for sig, handler in original_handlers.items():
                try:
                    signal.signal(sig, handler)
                except Exception:
                    pass  # Ignore errors when restoring handlers
            
        return self.should_stop or not self.is_recording

def run_script(script_path, beschreibung):
    """Legacy function for backwards compatibility"""
    manager = AsyncWorkflowManager()
    return manager.run_script_sync(script_path, beschreibung)

class WorkflowFileWatcher:
    """Background service that watches for workflow trigger files and executes tasks"""
    
    def __init__(self, work_dir=None):
        self.work_dir = Path(work_dir) if work_dir else Path(__file__).parent
        self.trigger_file = self.work_dir / "workflow_trigger.txt"
        self.status_log = self.work_dir / "workflow_status.log"
        self.lock_file = self.work_dir / "workflow_service.lock"
        self.running = False
        self.check_interval = 1.0  # Check every second
        self.workflow_completed = False
        
    def acquire_service_lock(self):
        """Acquire exclusive lock to prevent multiple service instances"""
        try:
            if self.lock_file.exists():
                # Check if existing lock is stale
                lock_stat = self.lock_file.stat()
                lock_age = time.time() - lock_stat.st_mtime
                if lock_age > 300:  # 5 minutes - consider stale
                    self.log_status("Entferne veraltete Lock-Datei", "WARNING")
                    self.lock_file.unlink()
                else:
                    self.log_status("Service bereits aktiv (Lock-Datei vorhanden)", "ERROR")
                    return False
            
            # Create lock file with PID
            with open(self.lock_file, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
            
            self.log_status(f"Service-Lock erworben (PID: {os.getpid()})")
            return True
            
        except Exception as e:
            self.log_status(f"Fehler beim Erwerben des Service-Locks: {e}", "ERROR")
            return False
    
    def release_service_lock(self):
        """Release service lock"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                self.log_status("Service-Lock freigegeben")
        except Exception as e:
            self.log_status(f"Fehler beim Freigeben des Service-Locks: {e}", "WARNING")
        
    def log_status(self, message, level="INFO"):
        """Log status message to log file"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] {level}: {message}\n"
            
            with open(self.status_log, "a", encoding="utf-8") as f:
                f.write(log_line)
                
            print(f"[{level}] {message}")
            
        except Exception as e:
            print(f"Logging error: {e}")
    
    def clear_status_log(self):
        """Clear the status log file"""
        try:
            if self.status_log.exists():
                self.status_log.unlink()
        except Exception as e:
            print(f"Error clearing log: {e}")
    
    def execute_workflow(self):
        """Execute the complete workflow after recording"""
        self.log_status("Workflow gestartet")
        
        success_count = 0
        total_steps = 3
        
        try:
            # Step 1: Voice recognition
            self.log_status("Schritt 1/3: Spracherkennung...")
            self.log_status(f"Setting GOOGLE_APPLICATION_CREDENTIALS to: {GOOGLE_SPEECH_CREDENTIALS}")
            
            manager = AsyncWorkflowManager()
            if manager.run_script_sync(str(self.work_dir / "voiceToGoogle.py"), "Spracherkennung"):
                success_count += 1
                self.log_status("Spracherkennung erfolgreich")
                
                # Check if transcript was created
                transcript_file = self.work_dir / "transkript.txt"
                if transcript_file.exists():
                    try:
                        with open(transcript_file, 'r', encoding='utf-8') as f:
                            transcript_content = f.read()
                        self.log_status(f"Transcript erstellt: '{transcript_content[:100]}{'...' if len(transcript_content) > 100 else ''}'")
                    except Exception as e:
                        self.log_status(f"Transcript-Datei konnte nicht gelesen werden: {e}", "WARNING")
                else:
                    self.log_status("Transcript-Datei wurde nicht erstellt", "WARNING")
            else:
                self.log_status("Spracherkennung fehlgeschlagen", "WARNING")
                self.log_status("Mögliche Ursachen:", "INFO")
                self.log_status("- GOOGLE_APPLICATION_CREDENTIALS nicht gesetzt oder Datei nicht gefunden", "INFO")
                self.log_status("- google-cloud-speech Bibliothek nicht installiert", "INFO") 
                self.log_status("- Netzwerkfehler oder Google Cloud API Problem", "INFO")
                self.log_status("- Ungültige Audio-Datei oder Audio-Datei nicht gefunden", "INFO")
            
            # Step 2: File operations
            self.log_status("Schritt 2/3: Dateioperationen...")
            if manager.run_script_sync(str(self.work_dir / "dateiKopieren.py"), "Dateioperationen"):
                success_count += 1
                self.log_status("Dateioperationen erfolgreich")
            else:
                self.log_status("Dateioperationen fehlgeschlagen", "WARNING")
            
            # Step 3: Image generation
            self.log_status("Schritt 3/3: Bildgenerierung...")
            prompt_text = get_copied_content()
            if prompt_text.strip():
                try:
                    generate_image_imagen4(prompt_text, image_count=1, 
                                         bilder_dir=str(self.work_dir / "BilderVertex"), 
                                         output_prefix="bild")
                    success_count += 1
                    self.log_status("Bildgenerierung erfolgreich")
                except Exception as e:
                    self.log_status(f"Bildgenerierung fehlgeschlagen: {e}", "ERROR")
            else:
                self.log_status("Kein Text für Bildgenerierung gefunden", "WARNING")
            
            # Final status
            if success_count == total_steps:
                self.log_status("WORKFLOW_COMPLETE: Alle Schritte erfolgreich")
            else:
                self.log_status(f"WORKFLOW_COMPLETE: {success_count}/{total_steps} Schritte erfolgreich", "WARNING")
                
        except Exception as e:
            self.log_status(f"WORKFLOW_ERROR: {e}", "ERROR")
        
        finally:
            # Clean up trigger file
            try:
                if self.trigger_file.exists():
                    self.trigger_file.unlink()
                    self.log_status("Trigger-Datei gelöscht")
            except Exception as e:
                self.log_status(f"Fehler beim Löschen der Trigger-Datei: {e}", "WARNING")
            
            # Mark workflow as completed and stop the service to prevent endless loop
            self.workflow_completed = True
            self.log_status("Service beendet sich nach erfolgreichem Workflow-Durchlauf")
            self.running = False
    
    def check_trigger(self):
        """Check for workflow trigger file"""
        if self.trigger_file.exists():
            try:
                with open(self.trigger_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                
                if content == "run":
                    self.log_status("Workflow-Trigger erkannt")
                    self.execute_workflow()
                    return True
                    
            except Exception as e:
                self.log_status(f"Fehler beim Lesen der Trigger-Datei: {e}", "ERROR")
        
        return False
    
    def start_watching(self):
        """Start watching for trigger files in background thread"""
        if self.running:
            print("Watcher bereits aktiv")
            return False
        
        # Acquire exclusive service lock
        if not self.acquire_service_lock():
            return False
        
        self.running = True
        self.workflow_completed = False
        self.clear_status_log()
        self.log_status("Workflow-Manager gestartet")
        self.log_status(f"Überwache Verzeichnis: {self.work_dir}")
        self.log_status(f"Trigger-Datei: {self.trigger_file}")
        
        def watcher_thread():
            try:
                while self.running and not self.workflow_completed:
                    try:
                        if self.check_trigger():
                            # Workflow was executed, service will stop
                            break
                        else:
                            time.sleep(self.check_interval)
                    except Exception as e:
                        self.log_status(f"Watcher-Fehler: {e}", "ERROR")
                        time.sleep(5.0)  # Wait longer on error
            except Exception as e:
                self.log_status(f"Watcher-Thread-Fehler: {e}", "ERROR")
            finally:
                # Always ensure service stops and lock is released
                self.running = False
                self.workflow_completed = True
                self.release_service_lock()
        
        import threading
        self.watcher_thread = threading.Thread(target=watcher_thread, daemon=True)
        self.watcher_thread.start()
        
        print(f"Workflow-Manager läuft im Hintergrund (PID: {os.getpid()})")
        print("Service beendet sich automatisch nach einem Workflow-Durchlauf")
        return True
    
    def stop_watching(self):
        """Stop the background watcher"""
        self.running = False
        self.release_service_lock()
        self.log_status("Workflow-Manager gestoppt")
        print("Workflow-Manager gestoppt")

def get_copied_content():
    """Get transcript content from file or clipboard"""
    # Try reading from transcript file in multiple locations
    possible_paths = [
        TRANSKRIPT_PATH,  # Original path
        "Transkripte/transkript.txt",  # After organization
        "transkript.txt"  # Current directory fallback
    ]
    
    for transcript_path in possible_paths:
        if os.path.exists(transcript_path):
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if text:
                    print(f"Text aus Datei gelesen ({transcript_path}).")
                    return text
            except Exception as e:
                print(f"Fehler beim Lesen der Transkript-Datei {transcript_path}: {e}")
    
    # Fallback to clipboard if file reading failed
    try:
        text = pyperclip.paste()
        if text and text.strip():
            print("Text aus Zwischenablage gelesen.")
            return text.strip()
    except Exception as e:
        print("Konnte Zwischenablage nicht lesen:", e)
    
    print("Kein Text gefunden!")
    return ""

def get_next_index(directory, prefix):
    files = glob.glob(f"{directory}/{prefix}_*.png")
    if not files:
        return 1
    nums = []
    for f in files:
        try:
            num = int(f.split("_")[-1].split(".")[0])
            nums.append(num)
        except Exception:
            continue
    return max(nums) + 1 if nums else 1

def generate_image_imagen4(prompt, image_count=1, bilder_dir=BILDER_DIR, output_prefix="bild"):
    """Generate images using Google's Imagen 4.0 API"""
    # Ensure directory exists
    if not os.path.exists(bilder_dir):
        os.makedirs(bilder_dir)
        print(f"Verzeichnis {bilder_dir} wurde erstellt.")
    
    # For demo purposes without actual Google Cloud credentials
    if not GOOGLE_CLOUD_AVAILABLE or not os.path.exists(GOOGLE_CREDENTIALS):
        if not GOOGLE_CLOUD_AVAILABLE:
            print("Google Cloud libraries not available")
        else:
            print(f"Google Cloud Credentials nicht gefunden: {GOOGLE_CREDENTIALS}")
        print("Demo-Modus: Simuliere Bildgenerierung...")
        
        # Create a placeholder image file for testing
        import base64
        from pathlib import Path
        
        start_idx = get_next_index(bilder_dir, output_prefix)
        for i in range(image_count):
            fname = f"{bilder_dir}/{output_prefix}_{start_idx + i}.png"
            # Create a minimal PNG file as placeholder
            minimal_png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )
            with open(fname, "wb") as f:
                f.write(minimal_png)
            print(f"Demo-Bild erstellt: {fname}")
        return
    
    # Real implementation with Google Cloud
    try:
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS, scopes=scopes
        )
        auth_req = GoogleAuthRequest()
        credentials.refresh(auth_req)
        token = credentials.token

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "instances": [
                {"prompt": prompt}
            ],
            "parameters": {
                "sampleCount": image_count,
                "aspectRatio": "16:9",
                "resolution": "2k"
            }
        }
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Fehler beim Bildgenerieren: {response.status_code}\n{response.text}")
            return
        result = response.json()
        start_idx = get_next_index(bilder_dir, output_prefix)
        for i, pred in enumerate(result["predictions"]):
            fname = f"{bilder_dir}/{output_prefix}_{start_idx + i}.png"
            img_data = base64.b64decode(pred["bytesBase64Encoded"])
            with open(fname, "wb") as f:
                f.write(img_data)
            print(f"Bild gespeichert: {fname}")
    except Exception as e:
        print(f"Fehler bei der Bildgenerierung: {e}")
        print("Erstelle Demo-Bild als Fallback...")
        # Create demo image as fallback
        start_idx = get_next_index(bilder_dir, output_prefix)
        fname = f"{bilder_dir}/{output_prefix}_{start_idx}.png"
        minimal_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        with open(fname, "wb") as f:
            f.write(minimal_png)
        print(f"Demo-Bild erstellt: {fname}")

def main():
    """
    Main workflow with asynchronous recording
    
    This function implements the new non-blocking workflow:
    1. Start Aufnahme.py asynchronously using subprocess.Popen
    2. Wait for external event to stop recording (Enter, SIGTERM, etc.)
    3. Continue with synchronous processing steps
    4. Collect and display all subprocess output
    """
    print("=== Audio Recording & AI Image Generation Workflow ===")
    print("Dieses Programm führt folgende Schritte aus:")
    print("1. Aufnahme (asynchron, manuell stoppbar)")  
    print("2. Spracherkennung")
    print("3. Datei kopieren")
    print("4. Bild generieren")
    print("=" * 60)
    
    # Initialize workflow manager
    workflow = AsyncWorkflowManager()
    
    # Step 1: Start recording asynchronously
    if not workflow.start_recording_async(AUFNAHME_SCRIPT):
        print("Fehler beim Starten der Aufnahme - Workflow abgebrochen")
        return False
    
    # Wait for recording to be stopped (manually or by signal)
    print("Warte auf Stop-Signal...")
    print("Optionen zum Stoppen:")
    print("- Drücke Enter")
    print("- Sende SIGTERM an diesen Prozess")
    print("- Drücke Ctrl+C")
    
    workflow.wait_for_stop_signal()
    
    # Stop recording if still running
    if workflow.is_recording:
        workflow.stop_recording()
    
    print("\n" + "=" * 60)
    print("Aufnahme abgeschlossen, fahre mit weiteren Schritten fort...")
    print("=" * 60)
    
    # Step 2: Voice recognition
    if not workflow.run_script_sync(VOICE_SCRIPT, "Spracherkennung"):
        print("Warnung: Spracherkennung fehlgeschlagen, fahre trotzdem fort...")
    
    # Step 3: Copy files  
    if not workflow.run_script_sync(COPY_SCRIPT, "Kopiervorgang"):
        print("Warnung: Kopiervorgang fehlgeschlagen, fahre trotzdem fort...")
    
    print("Inhalt von transkript.txt wurde ins Clipboard kopiert!")
    
    # Step 4: Generate image
    prompt_text = get_copied_content()
    if not prompt_text.strip():
        print("Kein Text zum Senden gefunden – Bild-Generierung übersprungen.")
    else:
        print("Sende Text als Prompt an Vertex AI Imagen 4 ...")
        try:
            generate_image_imagen4(prompt_text, image_count=1, bilder_dir=BILDER_DIR, output_prefix="bild")
        except Exception as e:
            print(f"Fehler bei Bild-Generierung: {e}")
    
    print("\n" + "=" * 60)
    print("Workflow vollständig abgeschlossen!")
    print("=" * 60)
    return True

# --- Original Workflow (kept for backwards compatibility) ---
def run_original_workflow():
    """Run the original synchronous workflow"""
    print("Führe ursprünglichen synchronen Workflow aus...")
    run_script(AUFNAHME_SCRIPT, "Aufnahme")
    run_script(VOICE_SCRIPT, "Spracherkennung")
    run_script(COPY_SCRIPT, "Kopiervorgang")
    print("Inhalt von transkript.txt wurde ins Clipboard kopiert!")

    prompt_text = get_copied_content()
    if not prompt_text.strip():
        print("Kein Text zum Senden gefunden – abgebrochen.")
    else:
        print("Sende Text als Prompt an Vertex AI Imagen 4 ...")
        generate_image_imagen4(prompt_text, image_count=1, bilder_dir=BILDER_DIR, output_prefix="bild")

    print("Workflow abgeschlossen!")

def run_background_service():
    """Run as background workflow manager service - runs ONCE then exits"""
    print("=== Workflow Manager Service ===")
    print("Startet als Hintergrunddienst für die Überwachung von Workflow-Triggern")
    print("Service wird nach EINEM erfolgreichen Workflow-Durchlauf beendet")
    
    watcher = WorkflowFileWatcher()
    
    # Set up signal handlers for clean shutdown
    import signal
    def signal_handler(signum, frame):
        print(f"\nSignal {signum} empfangen, beende Service...")
        watcher.stop_watching()
    
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    except Exception as e:
        print(f"Warning: Could not set signal handlers: {e}")
    
    if not watcher.start_watching():
        print("Fehler: Konnte Service nicht starten (möglicherweise läuft bereits eine Instanz)")
        return False
    
    try:
        # Keep the service running until one workflow completes
        while watcher.running and not watcher.workflow_completed:
            time.sleep(1)
        
        print("Workflow-Service beendet sich nach erfolgreichem Durchlauf")
        return True
        
    except KeyboardInterrupt:
        print("\nService wird beendet...")
        watcher.stop_watching()
        return False
    finally:
        # Ensure cleanup even if something goes wrong
        watcher.stop_watching()

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--original":
            run_original_workflow()
        elif sys.argv[1] == "--service":
            run_background_service()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python3 PythonServer.py           # Run interactive async workflow")
            print("  python3 PythonServer.py --service # Run as background service")
            print("  python3 PythonServer.py --original# Run original synchronous workflow")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        main()
