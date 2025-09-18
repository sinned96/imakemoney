import requests
import os
import base64
import logging
from PIL import Image, ImageOps

def setup_projekt_logging():
    """Setup unified logging for projekt.log and console output"""
    import logging
    from pathlib import Path
    # Use standardized base directory, but fall back to current directory if not accessible
    try:
        log_dir = Path("/home/pi/Desktop/v2_Tripple S")
        log_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Fallback to current working directory for testing/development
        log_dir = Path.cwd()
        
    log_file = log_dir / "projekt.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s [%(name)s]: %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_projekt_logging()

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
    logger.info(f"Starting image scaling to 1920x1080: {image_path}")
    try:
        with Image.open(image_path) as img:
            target_size = (1920, 1080)
            logger.info(f"Original image size: {img.size}")
            
            if preserve_aspect_ratio:
                # Use ImageOps.fit to maintain aspect ratio and fill the target size
                scaled_img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
                logger.info("Scaling with preserved aspect ratio")
            else:
                # Use resize to stretch to exact dimensions
                scaled_img = img.resize(target_size, Image.Resampling.LANCZOS)
                logger.info("Scaling without preserving aspect ratio")
            
            # Save the scaled image back to the same path
            scaled_img.save(image_path, "PNG")
            logger.info(f"Image successfully scaled to 1920x1080: {image_path}")
            print(f"Bild erfolgreich auf 1920x1080 skaliert: {image_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error scaling image {image_path}: {e}")
        print(f"Fehler beim Skalieren des Bildes {image_path}: {e}")
        return False

def main():
    logger.info("=== Vertex AI Image Workflow Started ===")
    
    if not os.path.exists(TRANSCRIPT_PATH):
        logger.error(f"Transcript not found: {TRANSCRIPT_PATH}")
        print(f"Transkript nicht gefunden: {TRANSCRIPT_PATH}")
        return

    try:
        with open(TRANSCRIPT_PATH, "r", encoding='utf-8') as f:
            prompt = f.read().strip()
        logger.info(f"Transcript loaded: {len(prompt)} characters")
    except Exception as e:
        logger.error(f"Error reading transcript file: {e}")
        print(f"Fehler beim Lesen des Transkripts: {e}")
        return

    if not prompt:
        logger.warning("Transcript is empty")
        print("Transkript ist leer!")
        return

    # Enhance prompt to specify German language
    enhanced_prompt = f"Sprache: Deutsch\n{prompt}"
    logger.info(f"Prompt enhanced with German language specification")
    logger.info(f"Sending prompt to Vertex AI: {enhanced_prompt[:100]}...")

    try:
        response = requests.post(
            ENDPOINT,
            json={"prompt": enhanced_prompt},
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=30  # Add timeout for better error handling
        )
        
        logger.info(f"Vertex AI response status: {response.status_code}")

        try:
            response.raise_for_status()
            data = response.json()
            if "image" in data:
                logger.info("Image data received from Vertex AI")
                img_bytes = base64.b64decode(data["image"])
                
                # Ensure directory exists
                os.makedirs(BILDER_DIR, exist_ok=True)
                logger.info(f"Output directory ensured: {BILDER_DIR}")
                
                img_path = os.path.join(BILDER_DIR, "vertex_output.png")
                
                with open(img_path, "wb") as img_file:
                    img_file.write(img_bytes)
                
                logger.info(f"Image successfully saved: {img_path}")
                print(f"Bild erfolgreich gespeichert: {img_path}")
                
                # Scale the image to 1920x1080 to fill screen completely
                if scale_image_to_1920x1080(img_path, preserve_aspect_ratio=True):
                    logger.info("Image scaled to 1920x1080 successfully")
                    print("Bild wurde auf 1920x1080 skaliert und füllt nun den Bildschirm komplett aus")
                else:
                    logger.warning("Image scaling failed")
                    print("Warnung: Bild konnte nicht skaliert werden, schwarze Balken können auftreten")
            else:
                logger.warning(f"No image in Vertex AI response: {data}")
                print("Kein Bild in der Antwort:", data)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Vertex AI request failed: {e}")
            print(f"Fehler beim Vertex-Request: {e}")
        except Exception as e:
            logger.error(f"Error processing Vertex AI response: {e}")
            print(f"Fehler beim Vertex-Request: {e}\nAntwort: {response.text}")
            
    except Exception as e:
        logger.error(f"Unexpected error in Vertex AI workflow: {e}", exc_info=True)
        print(f"Unerwarteter Fehler: {e}")
    
    logger.info("Vertex AI Image Workflow completed")

if __name__ == "__main__":
    main()
