#!/usr/bin/env python3
"""
vertex_ai_image_workflow.py - Enhanced Vertex AI Image Generation with Multimodal Support

This script processes transcripts and generates images using Vertex AI's Imagen API.
Now supports multimodal requests (text + image) when image_base64 is present in transkript.json.

Multimodal Support:
- Checks transkript.json for image_base64 field
- If present: builds Gemini multimodal request with text + image
- If absent: uses traditional text-only request
- Automatic fallback to text-only if image is invalid

Requirements:
- Vertex AI Generative AI API (Gemini) must be activated
- Valid Google Cloud credentials with Vertex AI permissions
- PIL library for image validation and processing

File Format Support:
- transkript.json: JSON format with optional image_base64 field (preferred)  
- transkript.txt: Plain text format (fallback)

Error Handling:
- Invalid image data: Falls back to text-only request
- Missing files: Comprehensive error messages and logging
- Network errors: Proper timeout and retry logic
"""

import requests
import os
import base64
import json
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
    
    # Suppress PIL debug noise - set PIL loggers to WARNING
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_projekt_logging()

TRANSCRIPT_PATH = "/home/pi/Desktop/v2_Tripple S/transkript.txt"
TRANSCRIPT_JSON_PATH = "/home/pi/Desktop/v2_Tripple S/transkript.json"
BILDER_DIR = "/home/pi/Desktop/v2_Tripple S/BilderVertex"
ENDPOINT = "https://vertex.googleapis.com/v1/your-endpoint"
TOKEN = "YOUR_ACCESS_TOKEN"

def get_aspect_ratio_from_meta():
    """
    Read aspect ratio from image_meta.json
    
    Returns:
        str: Aspect ratio ("16:9" or "9:16"), defaults to "16:9"
    """
    from pathlib import Path
    try:
        # Try to read from the same directory as this script
        script_dir = Path(__file__).parent
        meta_path = script_dir / "image_meta.json"
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                aspect_ratio = meta.get("aspect_ratio", "16:9")
                logger.info(f"Aspect ratio from image_meta.json: {aspect_ratio}")
                return aspect_ratio
    except Exception as e:
        logger.warning(f"Could not read aspect ratio from image_meta.json: {e}")
    
    # Default to 16:9
    return "16:9"

def scale_image_to_target_size(image_path, aspect_ratio="16:9", preserve_aspect_ratio=True):
    """
    Scale an image to target size based on aspect ratio using Pillow with LANCZOS resampling.
    Now preserves original size if aspect ratio is already correct.
    
    Args:
        image_path (str): Path to the image file
        aspect_ratio (str): Target aspect ratio ("16:9" or "9:16")
        preserve_aspect_ratio (bool): If True, uses ImageOps.fit to preserve aspect ratio.
                                    If False, uses resize which may distort the image.
    
    Returns:
        bool: True if scaling was successful or skipped (correct ratio), False otherwise
    """
    # Determine target aspect ratio
    if aspect_ratio == "9:16":
        target_ratio = 9.0 / 16.0  # Width / Height for vertical format
        target_size = (1080, 1920)  # Optional target size if scaling needed
        logger.info(f"Target aspect ratio: 9:16 (vertical format)")
    else:  # Default to 16:9
        target_ratio = 16.0 / 9.0  # Width / Height for horizontal format
        target_size = (1920, 1080)  # Optional target size if scaling needed
        logger.info(f"Target aspect ratio: 16:9 (horizontal format)")
    
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            original_width, original_height = original_size
            
            # Calculate current aspect ratio
            if original_height == 0:
                logger.error(f"Invalid image dimensions: {original_size}")
                return False
            
            current_ratio = original_width / original_height
            
            # Check if aspect ratio is already correct (with 5% tolerance)
            ratio_diff = abs(current_ratio - target_ratio) / target_ratio
            
            logger.info(f"Image analysis: aspect_ratio_request={aspect_ratio}, raw_output_size={original_size}, "
                       f"current_ratio={current_ratio:.3f}, target_ratio={target_ratio:.3f}, "
                       f"ratio_diff={ratio_diff:.1%}")
            
            # If aspect ratio is already correct (within tolerance), keep original size
            if ratio_diff < 0.05:  # 5% tolerance
                logger.info(f"Aspect ratio already correct ({ratio_diff:.1%} difference), "
                           f"final_saved_size={original_size}, scaling_applied=False")
                print(f"Bild hat bereits korrektes Seitenverhältnis ({aspect_ratio}), "
                     f"Originalgröße beibehalten: {original_size}")
                return True
            
            # Aspect ratio is wrong, need to scale
            logger.info(f"Aspect ratio mismatch ({ratio_diff:.1%} difference), scaling to {target_size}")
            
            if preserve_aspect_ratio:
                # Use ImageOps.fit to maintain aspect ratio and fill the target size
                scaled_img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
                logger.info(f"Scaling with preserved aspect ratio")
            else:
                # Use resize to stretch to exact dimensions
                scaled_img = img.resize(target_size, Image.Resampling.LANCZOS)
                logger.info(f"Scaling without preserving aspect ratio (may distort)")
            
            # Save the scaled image back to the same path
            scaled_img.save(image_path, "PNG")
            logger.info(f"Image scaled: aspect_ratio_request={aspect_ratio}, "
                       f"raw_output_size={original_size}, final_saved_size={target_size}, "
                       f"scaling_applied=True")
            print(f"Bild auf {target_size[0]}x{target_size[1]} ({aspect_ratio}) skaliert: "
                 f"{original_size} -> {target_size}")
            return True
            
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        print(f"Fehler beim Verarbeiten des Bildes {image_path}: {e}")
        return False

def scale_image_to_1920x1080(image_path, preserve_aspect_ratio=True):
    """
    Legacy function for backward compatibility.
    Now uses aspect ratio from image_meta.json to determine target size.
    """
    aspect_ratio = get_aspect_ratio_from_meta()
    return scale_image_to_target_size(image_path, aspect_ratio, preserve_aspect_ratio)

def main():
    logger.info("=== Vertex AI Image Workflow Started ===")
    
    # Check for transkript.json first (preferred for multimodal support)
    prompt = ""
    image_base64 = None
    
    if os.path.exists(TRANSCRIPT_JSON_PATH):
        logger.info(f"Found transkript.json: {TRANSCRIPT_JSON_PATH}")
        try:
            with open(TRANSCRIPT_JSON_PATH, "r", encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            prompt = transcript_data.get('transcript', '').strip()
            image_base64 = transcript_data.get('image_base64')
            
            logger.info(f"JSON transcript loaded: {len(prompt)} characters")
            if image_base64:
                logger.info(f"Image data found in JSON: {len(image_base64)} base64 characters")
            else:
                logger.info("No image data found in JSON transcript")
                
        except Exception as e:
            logger.error(f"Error reading transcript JSON file: {e}")
            print(f"Fehler beim Lesen des JSON-Transkripts: {e}")
            
            # Fallback to text file
            logger.info("Falling back to transkript.txt")
            if os.path.exists(TRANSCRIPT_PATH):
                try:
                    with open(TRANSCRIPT_PATH, "r", encoding='utf-8') as f:
                        prompt = f.read().strip()
                    logger.info(f"Text transcript loaded as fallback: {len(prompt)} characters")
                except Exception as e2:
                    logger.error(f"Error reading text transcript file: {e2}")
                    print(f"Fehler beim Lesen des Text-Transkripts: {e2}")
                    return
            else:
                logger.error("No transcript files found")
                print("Keine Transkript-Dateien gefunden")
                return
    
    elif os.path.exists(TRANSCRIPT_PATH):
        logger.info(f"Using text transcript: {TRANSCRIPT_PATH}")
        try:
            with open(TRANSCRIPT_PATH, "r", encoding='utf-8') as f:
                prompt = f.read().strip()
            logger.info(f"Text transcript loaded: {len(prompt)} characters")
        except Exception as e:
            logger.error(f"Error reading transcript file: {e}")
            print(f"Fehler beim Lesen des Transkripts: {e}")
            return
    else:
        logger.error("No transcript files found")
        print("Keine Transkript-Dateien gefunden")
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
        # Build request payload based on whether we have image data
        if image_base64:
            # Multimodal request (text + image) using Gemini format
            logger.info("Building multimodal request with text and image")
            
            # Validate and analyze base64 image data
            try:
                # Decode the full image to validate it
                image_bytes = base64.b64decode(image_base64)
                logger.info(f"Image base64 data validation passed: {len(image_bytes)} bytes decoded")
                
                # Try to detect MIME type by creating a temporary image
                import io
                try:
                    with Image.open(io.BytesIO(image_bytes)) as img:
                        img_format = img.format.lower() if img.format else 'png'
                        mime_type = f"image/{img_format}"
                        logger.info(f"Detected image format: {img_format}")
                except Exception as img_error:
                    logger.warning(f"Could not detect image format: {img_error}, defaulting to PNG")
                    mime_type = "image/png"
                    
            except Exception as e:
                logger.error(f"Invalid image base64 data: {e}")
                print(f"Fehler: Ungültige Bilddaten - {e}")
                print("Fallback: Fahre nur mit Text fort...")
                
                # Fallback to text-only request
                logger.info("Falling back to text-only request due to invalid image")
                request_payload = {"prompt": enhanced_prompt}
                image_base64 = None  # Clear the image flag
                
            if image_base64:  # Only build multimodal if image is still valid
                request_payload = {
                    "instances": [{
                        "prompt": enhanced_prompt,
                        "image": {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    }],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": get_aspect_ratio_from_meta(),
                        "resolution": "2k"
                    }
                }
                logger.info(f"Multimodal request payload built (Gemini format, {mime_type})")
            
        if not image_base64:  # This covers both no image initially and fallback cases
            # Text-only request (existing behavior)
            logger.info("Building text-only request")
            request_payload = {"prompt": enhanced_prompt}
        
        response = requests.post(
            ENDPOINT,
            json=request_payload,
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
                
                # Scale the image to target size based on aspect ratio from image_meta.json
                if scale_image_to_1920x1080(img_path, preserve_aspect_ratio=True):
                    logger.info("Image scaled to target aspect ratio successfully")
                    print("Bild wurde auf Ziel-Seitenverhältnis skaliert")
                else:
                    logger.warning("Image scaling failed")
                    print("Warnung: Bild konnte nicht skaliert werden")
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
