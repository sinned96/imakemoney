import requests
import os
import base64
from PIL import Image, ImageOps

TRANSCRIPT_PATH = "/home/pi/Desktop/v2_Tripple S/transkript.txt"
BILDER_DIR = "/home/pi/Desktop/v2_Tripple S/BilderVertex"
ENDPOINT = "https://vertex.googleapis.com/v1/your-endpoint"
TOKEN = "YOUR_ACCESS_TOKEN"

def scale_image_to_1920x1080(image_path, preserve_aspect_ratio=True):
    """
    Scale an image to 1920x1080 pixels using Pillow with LANCZOS resampling.
    
    Args:
        image_path (str): Path to the image file
        preserve_aspect_ratio (bool): If True, uses ImageOps.fit to preserve aspect ratio.
                                    If False, uses resize which may distort the image.
    
    Returns:
        bool: True if scaling was successful, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            target_size = (1920, 1080)
            
            if preserve_aspect_ratio:
                # Use ImageOps.fit to maintain aspect ratio and fill the target size
                scaled_img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
            else:
                # Use resize to stretch to exact dimensions
                scaled_img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save the scaled image back to the same path
            scaled_img.save(image_path, "PNG")
            print(f"Bild erfolgreich auf 1920x1080 skaliert: {image_path}")
            return True
            
    except Exception as e:
        print(f"Fehler beim Skalieren des Bildes {image_path}: {e}")
        return False

def main():
    if not os.path.exists(TRANSCRIPT_PATH):
        print(f"Transkript nicht gefunden: {TRANSCRIPT_PATH}")
        return

    with open(TRANSCRIPT_PATH, "r") as f:
        prompt = f.read().strip()

    if not prompt:
        print("Transkript ist leer!")
        return

    response = requests.post(
        ENDPOINT,
        json={"prompt": prompt},
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
    )

    try:
        response.raise_for_status()
        data = response.json()
        if "image" in data:
            img_bytes = base64.b64decode(data["image"])
            os.makedirs(BILDER_DIR, exist_ok=True)
            img_path = os.path.join(BILDER_DIR, "vertex_output.png")
            with open(img_path, "wb") as img_file:
                img_file.write(img_bytes)
            print(f"Bild erfolgreich gespeichert: {img_path}")
            
            # Scale the image to 1920x1080 to fill screen completely
            if scale_image_to_1920x1080(img_path, preserve_aspect_ratio=True):
                print("Bild wurde auf 1920x1080 skaliert und füllt nun den Bildschirm komplett aus")
            else:
                print("Warnung: Bild konnte nicht skaliert werden, schwarze Balken können auftreten")
        else:
            print("Kein Bild in der Antwort:", data)
    except Exception as e:
        print(f"Fehler beim Vertex-Request: {e}\nAntwort: {response.text}")

if __name__ == "__main__":
    main()
