import requests
import os
import base64
from PIL import Image, ImageOps
from logging_config import setup_project_logging, log_function_entry, log_function_exit, log_exception

# Setup project logging
logger = setup_project_logging("vertex_ai_image_workflow")

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
    log_function_entry(logger, "scale_image_to_1920x1080", image_path=image_path, preserve_aspect_ratio=preserve_aspect_ratio)
    
    try:
        logger.info(f"Starting image scaling for: {image_path}")
        with Image.open(image_path) as img:
            original_size = img.size
            logger.debug(f"Original image size: {original_size}")
            
            target_size = (1920, 1080)
            logger.debug(f"Target size: {target_size}")
            
            if preserve_aspect_ratio:
                logger.debug("Using ImageOps.fit to maintain aspect ratio")
                # Use ImageOps.fit to maintain aspect ratio and fill the target size
                scaled_img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
            else:
                logger.debug("Using resize to stretch to exact dimensions")
                # Use resize to stretch to exact dimensions
                scaled_img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save the scaled image back to the same path
            scaled_img.save(image_path, "PNG")
            logger.info(f"Image successfully scaled to 1920x1080: {image_path}")
            print(f"Bild erfolgreich auf 1920x1080 skaliert: {image_path}")
            log_function_exit(logger, "scale_image_to_1920x1080", result=True)
            return True
            
    except Exception as e:
        error_msg = f"Error scaling image {image_path}: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"Fehler beim Skalieren des Bildes {image_path}: {e}")
        log_function_exit(logger, "scale_image_to_1920x1080", error=e)
        return False

def main():
    log_function_entry(logger, "main")
    logger.info("Starting Vertex AI image workflow")
    
    # Handle development/testing fallback paths
    transcript_path = TRANSCRIPT_PATH
    bilder_dir = BILDER_DIR
    
    # Check if using fallback paths for development
    if not os.path.exists(os.path.dirname(TRANSCRIPT_PATH)):
        logger.warning(f"Standard path not accessible: {TRANSCRIPT_PATH}")
        logger.info("Using fallback paths for development/testing environment")
        transcript_path = "transkript.txt"  # Current directory fallback
        bilder_dir = "BilderVertex"  # Current directory fallback
    
    logger.info(f"Using transcript path: {transcript_path}")
    logger.info(f"Using images directory: {bilder_dir}")
    
    if not os.path.exists(transcript_path):
        error_msg = f"Transcript not found: {transcript_path}"
        logger.error(error_msg)
        print(f"Transkript nicht gefunden: {transcript_path}")
        log_function_exit(logger, "main", error="Transcript file not found")
        return

    try:
        logger.info("Reading transcript file...")
        with open(transcript_path, "r", encoding='utf-8') as f:
            prompt = f.read().strip()
        
        logger.info(f"Original prompt length: {len(prompt)} characters")
        logger.debug(f"Original prompt content: {prompt}")

        if not prompt:
            error_msg = "Transcript is empty"
            logger.error(error_msg)
            print("Transkript ist leer!")
            log_function_exit(logger, "main", error="Empty transcript")
            return

        # ENHANCED: Always specify German language in the prompt
        # This ensures Vertex AI understands the content is German without automatic detection
        enhanced_prompt = f"Sprache: Deutsch\n{prompt}"
        logger.info("Enhanced prompt with German language specification")
        logger.debug(f"Enhanced prompt: {enhanced_prompt}")

        logger.info("Preparing request to Vertex AI Imagen API...")
        logger.debug(f"Endpoint: {ENDPOINT}")
        logger.debug(f"Prompt length after enhancement: {len(enhanced_prompt)} characters")

        response = requests.post(
            ENDPOINT,
            json={"prompt": enhanced_prompt},
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info(f"Received response from Vertex AI (status: {response.status_code})")

        try:
            response.raise_for_status()
            logger.info("Response status check passed")
            
            data = response.json()
            logger.debug(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if "image" in data:
                logger.info("Image data found in response, decoding...")
                img_bytes = base64.b64decode(data["image"])
                logger.info(f"Decoded image size: {len(img_bytes)} bytes")
                
                # Create output directory
                logger.debug(f"Creating output directory: {bilder_dir}")
                os.makedirs(bilder_dir, exist_ok=True)
                
                img_path = os.path.join(bilder_dir, "vertex_output.png")
                logger.info(f"Saving image to: {img_path}")
                
                with open(img_path, "wb") as img_file:
                    img_file.write(img_bytes)
                
                logger.info(f"Image successfully saved: {img_path}")
                print(f"Bild erfolgreich gespeichert: {img_path}")
                
                # Scale the image to 1920x1080 to fill screen completely
                logger.info("Starting image scaling process...")
                if scale_image_to_1920x1080(img_path, preserve_aspect_ratio=True):
                    logger.info("Image scaling completed successfully")
                    print("Bild wurde auf 1920x1080 skaliert und füllt nun den Bildschirm komplett aus")
                else:
                    logger.warning("Image scaling failed")
                    print("Warnung: Bild konnte nicht skaliert werden, schwarze Balken können auftreten")
                
                logger.info("Vertex AI image workflow completed successfully")
                log_function_exit(logger, "main", result=True)
            else:
                error_msg = f"No image in response: {data}"
                logger.error(error_msg)
                print("Kein Bild in der Antwort:", data)
                log_function_exit(logger, "main", error="No image in response")
        except requests.exceptions.HTTPError as http_err:
            error_msg = f"HTTP error from Vertex AI: {http_err}"
            logger.error(error_msg)
            logger.error(f"Response text: {response.text}")
            print(f"HTTP-Fehler beim Vertex-Request: {http_err}\nAntwort: {response.text}")
            log_function_exit(logger, "main", error=http_err)
        except Exception as e:
            error_msg = f"Error processing Vertex AI response: {e}"
            logger.error(error_msg, exc_info=True)
            logger.error(f"Response text: {response.text}")
            print(f"Fehler beim Vertex-Request: {e}\nAntwort: {response.text}")
            log_function_exit(logger, "main", error=e)
    except FileNotFoundError as e:
        error_msg = f"File not found: {e}"
        logger.error(error_msg)
        print(f"Datei nicht gefunden: {e}")
        log_function_exit(logger, "main", error=e)
    except Exception as e:
        error_msg = f"Unexpected error in main: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"Unerwarteter Fehler: {e}")
        log_function_exit(logger, "main", error=e)

if __name__ == "__main__":
    main()
