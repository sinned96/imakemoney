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
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest

GOOGLE_CREDENTIALS = "/home/pi/Desktop/v2_Tripple S/cloudKey.json"
PROJECT_ID = "trippe-s"
ENDPOINT = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/us-central1/publishers/google/models/imagen-4.0-generate-001:predict"

AUFNAHME_SCRIPT = "/home/pi/Desktop/v2_Tripple S/Aufnahme.py"
VOICE_SCRIPT = "/home/pi/Desktop/v2_Tripple S/Aufnahmen/voiceToGoogle.py"
COPY_SCRIPT = "/home/pi/Desktop/v2_Tripple S/Aufnahmen/dateiKopieren.py"
TRANSKRIPT_PATH = "transkript.txt"
BILDER_DIR = "/home/pi/Desktop/v2_Tripple S/BilderVertex"

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
                result = subprocess.run(
                    ["python3", script_path], 
                    capture_output=True, 
                    text=True,
                    timeout=300  # 5 minute timeout
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
        if not os.path.exists(script_path):
            print(f"Aufnahme-Script nicht gefunden: {script_path}")
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
        original_sigint = signal.signal(signal.SIGINT, signal_handler)
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.is_recording and not self.should_stop:
                # Check if recording process is still running
                if self.recording_process and self.recording_process.poll() is not None:
                    print("Aufnahme-Prozess beendet")
                    self.is_recording = False
                    break
                
                # Check for keyboard input (non-blocking)
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    input_line = sys.stdin.readline().strip()
                    if input_line == "" or input_line.lower() in ['q', 'quit', 'exit', 'stop']:
                        print("Benutzer-Stop erkannt")
                        self.should_stop = True
                        break
                        
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt empfangen")
            self.should_stop = True
        finally:
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            
        return self.should_stop or not self.is_recording

def run_script(script_path, beschreibung):
    """Legacy function for backwards compatibility"""
    manager = AsyncWorkflowManager()
    return manager.run_script_sync(script_path, beschreibung)

def get_copied_content():
    if os.path.exists(TRANSKRIPT_PATH):
        with open(TRANSKRIPT_PATH, "r", encoding="utf-8") as f:
            text = f.read()
        if text.strip():
            print("Text aus Datei gelesen.")
            return text
    try:
        text = pyperclip.paste()
        if text.strip():
            print("Text aus Zwischenablage gelesen.")
            return text
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
    if not os.path.exists(bilder_dir):
        os.makedirs(bilder_dir)
        print(f"Verzeichnis {bilder_dir} wurde erstellt.")
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
            "aspectRatio": "16:9",      # <-- Wichtig für breite Bilder!
            "resolution": "2k"          # <-- Wichtig für Full HD!
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

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--original":
        run_original_workflow()
    else:
        main()
