#!/usr/bin/env python3
"""
start_workflow_service.py - Utility to start the background workflow service

This script starts the PythonServer.py background service that watches for
workflow trigger files created by the GUI.
Now, after the workflow service completes, it automatically runs the Vertex-AI image generation step.
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

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

VERTEX_SCRIPT = "vertex_ai_image_workflow.py"
TRANSCRIPT_PATH = "transkript.txt"
BILDER_DIR = "BilderVertex"

def check_service_running():
    """Check if the workflow service is already running"""
    logger.info("Checking if workflow service is already running")
    try:
        script_dir = Path(__file__).parent
        lock_file = script_dir / "workflow_service.lock"
        
        if lock_file.exists():
            # Check if lock is recent (service might be running)
            stat = lock_file.stat()
            age = time.time() - stat.st_mtime
            if age < 30:
                logger.warning(f"Workflow service appears to be running (lock file: {lock_file}, age: {age:.1f}s)")
                print(f"Workflow-Service scheint bereits zu laufen (Lock-Datei: {lock_file})")
                try:
                    with open(lock_file, "r") as f:
                        pid = f.read().strip()
                    logger.info(f"Service PID from lock file: {pid}")
                    print(f"Service-PID aus Lock-Datei: {pid}")
                except Exception as e:
                    logger.warning(f"Error reading lock file: {e}")
                return True
            else:
                logger.info(f"Found stale lock file ({age:.1f}s old), ignoring")
                print(f"Veraltete Lock-Datei gefunden ({age:.1f}s alt), ignoriere")
        
        # Also check for recent status log
        status_log = script_dir / "workflow_status.log"
        if status_log.exists():
            # Check if log was recently updated (within last 30 seconds)
            stat = status_log.stat()
            age = time.time() - stat.st_mtime
            if age < 30:
                logger.warning(f"Workflow service appears to be running (recent log file, age: {age:.1f}s)")
                print("Workflow-Service scheint bereits zu laufen (aktuelle Log-Datei gefunden)")
                return True
    except Exception as e:
        logger.error(f"Error checking service status: {e}")
    return False

def run_vertex_step(script_dir):
    """Run the Vertex AI image generation step if transcript exists"""
    logger.info("Starting Vertex AI image generation step")
    vertex_script = script_dir / VERTEX_SCRIPT
    transcript_file = script_dir / TRANSCRIPT_PATH
    bilder_dir = script_dir / BILDER_DIR

    print("\n--- Starte Vertex KI Bildgenerierungsschritt ---")
    if not vertex_script.exists():
        logger.error(f"Vertex script not found: {vertex_script}")
        print(f"Vertex-Skript nicht gefunden: {vertex_script}")
        return False
    if not transcript_file.exists():
        logger.error(f"Transcript not found: {transcript_file}")
        print(f"Transkript nicht gefunden: {transcript_file}")
        return False

    try:
        # Start Vertex image generation script
        logger.info(f"Executing vertex script: {vertex_script}")
        result = subprocess.run(
            [sys.executable, str(vertex_script)],
            cwd=str(script_dir),
            capture_output=True,
            text=True,
            timeout=120  # Add timeout for better error handling
        )
        
        if result.stdout:
            print(result.stdout)
            logger.info(f"Vertex script stdout: {result.stdout}")
            
        if result.returncode == 0:
            logger.info(f"Vertex AI image generation completed successfully")
            print(f"✓ Vertex KI Bildgenerierung abgeschlossen. Bild sollte in {bilder_dir} liegen.")
            return True
        else:
            logger.error(f"Vertex AI step failed with exit code: {result.returncode}")
            print(f"✗ Fehler beim Vertex KI Schritt! Code: {result.returncode}")
            if result.stderr:
                logger.error(f"Vertex script stderr: {result.stderr}")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Vertex script execution timed out")
        print("Fehler: Vertex KI Skript-Ausführung dauerte zu lange")
        return False
    except Exception as e:
        logger.error(f"Error executing Vertex AI script: {e}")
        print(f"Fehler beim Ausführen des Vertex KI Skripts: {e}")
        return False

def start_service():
    """Start the workflow service"""
    logger.info("Starting workflow service")
    script_dir = Path(__file__).parent
    server_script = script_dir / "PythonServer.py"
    
    if not server_script.exists():
        logger.error(f"PythonServer.py not found in {script_dir}")
        print(f"Fehler: PythonServer.py nicht gefunden in {script_dir}")
        return False
    
    logger.info(f"Starting workflow manager service: {server_script}")
    print("Starte Workflow-Manager Service...")
    print(f"Script: {server_script}")
    
    try:
        # Start the service as subprocess
        process = subprocess.Popen(
            [sys.executable, str(server_script), "--service"],
            cwd=str(script_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's still running
        if process.poll() is None:
            logger.info(f"Workflow manager service started successfully (PID: {process.pid})")
            print(f"✓ Workflow-Manager Service gestartet (PID: {process.pid})")
            print("Service läuft im Hintergrund und überwacht Workflow-Trigger")
            print("HINWEIS: Service beendet sich automatisch nach einem Workflow-Durchlauf")
            print(f"\nZum manuellen Beenden: kill {process.pid}")
            
            # Monitor the service briefly, then detach
            print("Überwache Service für 10 Sekunden...")
            for i in range(10):
                if process.poll() is not None:
                    logger.info(f"Service terminated (Exit Code: {process.returncode})")
                    print(f"Service beendet (Exit Code: {process.returncode})")
                    break
                time.sleep(1)
                print(".", end="", flush=True)
            
            if process.poll() is None:
                logger.info(f"Service running stable (PID: {process.pid})")
                print(f"\n✓ Service läuft stabil (PID: {process.pid})")
                print("Service wird im Hintergrund weitergeführt...")
                # Let it run in background and exit after one workflow
                return True
            else:
                stdout, stderr = process.communicate()
                logger.info(f"Service completed with exit code: {process.returncode}")
                print(f"Service beendet mit Exit Code: {process.returncode}")
                if stdout:
                    logger.info(f"Service stdout: {stdout}")
                    print("STDOUT:", stdout)
                if stderr:
                    logger.warning(f"Service stderr: {stderr}")
                    print("STDERR:", stderr)
                # Nach erfolgreichem Durchlauf: Vertex-Schritt!
                success = run_vertex_step(script_dir)
                return process.returncode == 0 and success
        else:
            stdout, stderr = process.communicate()
            logger.error("Service could not be started")
            print("✗ Service konnte nicht gestartet werden")
            if stdout:
                logger.error(f"Service stdout: {stdout}")
                print("STDOUT:", stdout)
            if stderr:
                logger.error(f"Service stderr: {stderr}")
                print("STDERR:", stderr)
            return False
            
    except Exception as e:
        logger.error(f"Error starting service: {e}")
        print(f"Fehler beim Starten des Service: {e}")
        return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Service Starter")
    parser.add_argument("--auto", action="store_true", 
                       help="Start automatically without prompts (for automation)")
    args = parser.parse_args()
    
    logger.info("=== Workflow Service Starter Started ===")
    print("=== Workflow Service Starter ===")
    
    if check_service_running():
        if args.auto:
            logger.info("Service appears to be running, auto mode: skipping start")
            print("Service scheint bereits zu laufen. Auto-Modus: Überspringe Start.")
            return
        else:
            response = input("Service scheint bereits zu laufen. Trotzdem starten? (j/N): ")
            if response.lower() not in ('j', 'ja', 'y', 'yes'):
                logger.info("User cancelled service start")
                print("Abgebrochen.")
                return
    
    if start_service():
        logger.info("Service started successfully")
        print("Service erfolgreich gestartet.")
    else:
        logger.error("Service could not be started")
        print("Service konnte nicht gestartet werden.")
        if not args.auto:
            sys.exit(1)

if __name__ == "__main__":
    main()
