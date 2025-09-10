import os
import base64
import subprocess
import pyperclip
import requests
import glob
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

def run_script(script_path, beschreibung):
    if os.path.exists(script_path):
        print(f"Starte {beschreibung}: {script_path}")
        result = subprocess.run(["python3", script_path])
        if result.returncode != 0:
            print(f"Fehler beim Starten von {os.path.basename(script_path)}.")
        else:
            print(f"{beschreibung} abgeschlossen!")
    else:
        print(f"{os.path.basename(script_path)} nicht gefunden!")

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

# --- Workflow ---
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
