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
from pathlib import Path
from logging_config import setup_project_logging, log_function_entry, log_function_exit, log_exception

# Setup project logging
logger = setup_project_logging("start_workflow_service")

VERTEX_SCRIPT = "vertex_ai_image_workflow.py"
TRANSCRIPT_PATH = "transkript.txt"
BILDER_DIR = "BilderVertex"

def check_service_running():
    """Check if the workflow service is already running"""
    log_function_entry(logger, "check_service_running")
    
    try:
        script_dir = Path(__file__).parent
        lock_file = script_dir / "workflow_service.lock"
        logger.debug(f"Checking lock file: {lock_file}")
        
        if lock_file.exists():
            # Check if lock is recent (service might be running)
            stat = lock_file.stat()
            age = time.time() - stat.st_mtime
            logger.debug(f"Lock file age: {age:.1f} seconds")
            
            if age < 30:
                logger.warning(f"Workflow service appears to be running (lock file: {lock_file})")
                print(f"Workflow-Service scheint bereits zu laufen (Lock-Datei: {lock_file})")
                try:
                    with open(lock_file, "r") as f:
                        pid = f.read().strip()
                    logger.info(f"Service PID from lock file: {pid}")
                    print(f"Service-PID aus Lock-Datei: {pid}")
                except Exception as e:
                    logger.debug(f"Could not read PID from lock file: {e}")
                    pass
                log_function_exit(logger, "check_service_running", result=True)
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
            logger.debug(f"Status log age: {age:.1f} seconds")
            
            if age < 30:
                logger.warning("Workflow service appears to be running (recent log file found)")
                print("Workflow-Service scheint bereits zu laufen (aktuelle Log-Datei gefunden)")
                log_function_exit(logger, "check_service_running", result=True)
                return True
                
        logger.info("No running service detected")
        log_function_exit(logger, "check_service_running", result=False)
        return False
        
    except Exception as e:
        logger.debug(f"Error checking service status: {e}")
        log_function_exit(logger, "check_service_running", error=e)
        return False

def run_vertex_step(script_dir):
    """Run the Vertex AI image generation step if transcript exists"""
    log_function_entry(logger, "run_vertex_step", script_dir=str(script_dir))
    
    vertex_script = script_dir / VERTEX_SCRIPT
    transcript_file = script_dir / TRANSCRIPT_PATH
    bilder_dir = script_dir / BILDER_DIR

    logger.info("Starting Vertex AI image generation step")
    print("\n--- Starte Vertex KI Bildgenerierungsschritt ---")
    
    if not vertex_script.exists():
        error_msg = f"Vertex script not found: {vertex_script}"
        logger.error(error_msg)
        print(f"Vertex-Skript nicht gefunden: {vertex_script}")
        log_function_exit(logger, "run_vertex_step", error=error_msg)
        return False
        
    if not transcript_file.exists():
        error_msg = f"Transcript not found: {transcript_file}"
        logger.error(error_msg)
        print(f"Transkript nicht gefunden: {transcript_file}")
        log_function_exit(logger, "run_vertex_step", error=error_msg)
        return False

    try:
        logger.info(f"Running Vertex AI script: {vertex_script}")
        # Start Vertex image generation script
        result = subprocess.run(
            [sys.executable, str(vertex_script)],
            cwd=str(script_dir),
            capture_output=True,
            text=True
        )
        
        logger.info(f"Vertex script completed with exit code: {result.returncode}")
        print(result.stdout)
        
        if result.returncode == 0:
            logger.info(f"Vertex AI image generation completed successfully")
            print(f"✓ Vertex KI Bildgenerierung abgeschlossen. Bild sollte in {bilder_dir} liegen.")
            log_function_exit(logger, "run_vertex_step", result=True)
            return True
        else:
            logger.error(f"Vertex AI step failed with exit code: {result.returncode}")
            print(f"✗ Fehler beim Vertex KI Schritt! Code: {result.returncode}")
            if result.stderr:
                logger.error(f"Stderr: {result.stderr}")
                print(result.stderr)
            log_function_exit(logger, "run_vertex_step", error=f"Exit code {result.returncode}")
            return False
            
    except Exception as e:
        error_msg = f"Error executing Vertex AI script: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"Fehler beim Ausführen des Vertex KI Skripts: {e}")
        log_function_exit(logger, "run_vertex_step", error=e)
        return False

def start_service():
    """Start the workflow service"""
    log_function_entry(logger, "start_service")
    
    script_dir = Path(__file__).parent
    server_script = script_dir / "PythonServer.py"
    
    if not server_script.exists():
        error_msg = f"PythonServer.py not found in {script_dir}"
        logger.error(error_msg)
        print(f"Fehler: PythonServer.py nicht gefunden in {script_dir}")
        log_function_exit(logger, "start_service", error=error_msg)
        return False
    
    logger.info("Starting Workflow Manager Service...")
    logger.info(f"Script: {server_script}")
    print("Starte Workflow-Manager Service...")
    print(f"Script: {server_script}")
    
    try:
        # Start the service as subprocess
        logger.debug("Creating service subprocess...")
        process = subprocess.Popen(
            [sys.executable, str(server_script), "--service"],
            cwd=str(script_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Give it a moment to start
        logger.debug("Waiting for service to initialize...")
        time.sleep(2)
        
        # Check if it's still running
        if process.poll() is None:
            logger.info(f"Workflow Manager Service started successfully (PID: {process.pid})")
            print(f"✓ Workflow-Manager Service gestartet (PID: {process.pid})")
            print("Service läuft im Hintergrund und überwacht Workflow-Trigger")
            print("HINWEIS: Service beendet sich automatisch nach einem Workflow-Durchlauf")
            print(f"\nZum manuellen Beenden: kill {process.pid}")
            
            # Monitor the service briefly, then detach
            logger.info("Monitoring service for 10 seconds...")
            print("Überwache Service für 10 Sekunden...")
            
            for i in range(10):
                if process.poll() is not None:
                    logger.info(f"Service terminated (Exit Code: {process.returncode})")
                    print(f"Service beendet (Exit Code: {process.returncode})")
                    break
                time.sleep(1)
                print(".", end="", flush=True)
            
            if process.poll() is None:
                logger.info(f"Service running stably (PID: {process.pid})")
                print(f"\n✓ Service läuft stabil (PID: {process.pid})")
                print("Service wird im Hintergrund weitergeführt...")
                # Let it run in background and exit after one workflow
                log_function_exit(logger, "start_service", result=True)
                return True
            else:
                # Service completed, get output
                stdout, stderr = process.communicate()
                logger.info(f"Service completed with exit code: {process.returncode}")
                print(f"Service beendet mit Exit Code: {process.returncode}")
                
                if stdout:
                    logger.debug(f"Service stdout: {stdout}")
                    print("STDOUT:", stdout)
                if stderr:
                    logger.debug(f"Service stderr: {stderr}")
                    print("STDERR:", stderr)
                    
                # After successful completion: run Vertex step
                logger.info("Service completed, running Vertex AI step...")
                run_vertex_step(script_dir)
                log_function_exit(logger, "start_service", result=(process.returncode == 0))
                return process.returncode == 0
        else:
            # Service failed to start
            stdout, stderr = process.communicate()
            logger.error("Service could not be started")
            print("✗ Service konnte nicht gestartet werden")
            
            if stdout:
                logger.debug(f"Failed service stdout: {stdout}")
                print("STDOUT:", stdout)
            if stderr:
                logger.error(f"Failed service stderr: {stderr}")
                print("STDERR:", stderr)
                
            log_function_exit(logger, "start_service", error="Service startup failed")
            return False
            
    except Exception as e:
        error_msg = f"Error starting service: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"Fehler beim Starten des Service: {e}")
        log_function_exit(logger, "start_service", error=e)
        return False

def main():
    """Main entry point"""
    log_function_entry(logger, "main")
    logger.info("Starting Workflow Service Starter")
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Service Starter")
    parser.add_argument("--auto", action="store_true", 
                       help="Start automatically without prompts (for automation)")
    args = parser.parse_args()
    
    logger.info(f"Arguments: auto={args.auto}")
    print("=== Workflow Service Starter ===")
    
    if check_service_running():
        if args.auto:
            logger.info("Service appears to be running, auto-mode: skipping start")
            print("Service scheint bereits zu laufen. Auto-Modus: Überspringe Start.")
            log_function_exit(logger, "main", result="skipped")
            return
        else:
            response = input("Service scheint bereits zu laufen. Trotzdem starten? (j/N): ")
            logger.info(f"User response to running service: '{response}'")
            if response.lower() not in ('j', 'ja', 'y', 'yes'):
                logger.info("User chose to abort")
                print("Abgebrochen.")
                log_function_exit(logger, "main", result="aborted")
                return
    
    logger.info("Starting workflow service...")
    if start_service():
        logger.info("Service started successfully")
        print("Service erfolgreich gestartet.")
        log_function_exit(logger, "main", result=True)
    else:
        logger.error("Service could not be started")
        print("Service konnte nicht gestartet werden.")
        if not args.auto:
            sys.exit(1)
        log_function_exit(logger, "main", error="Service startup failed")

if __name__ == "__main__":
    main()
