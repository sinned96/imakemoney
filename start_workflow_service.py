#!/usr/bin/env python3
"""
start_workflow_service.py - Utility to start the background workflow service

This script starts the PythonServer.py background service that watches for
workflow trigger files created by the GUI.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_service_running():
    """Check if the workflow service is already running"""
    try:
        # Simple check - look for existing status log
        status_log = Path(__file__).parent / "workflow_status.log"
        if status_log.exists():
            # Check if log was recently updated (within last 30 seconds)
            stat = status_log.stat()
            age = time.time() - stat.st_mtime
            if age < 30:
                print("Workflow-Service scheint bereits zu laufen (aktuelle Log-Datei gefunden)")
                return True
    except Exception:
        pass
    return False

def start_service():
    """Start the workflow service"""
    script_dir = Path(__file__).parent
    server_script = script_dir / "PythonServer.py"
    
    if not server_script.exists():
        print(f"Fehler: PythonServer.py nicht gefunden in {script_dir}")
        return False
    
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
            print(f"✓ Workflow-Manager Service gestartet (PID: {process.pid})")
            print("Service läuft im Hintergrund und überwacht Workflow-Trigger")
            print("\nZum Beenden: Strg+C oder kill -TERM {}".format(process.pid))
            
            # Keep monitoring (optional - could also just exit here)
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\nBeende Service...")
                process.terminate()
                process.wait()
                
            return True
        else:
            stdout, stderr = process.communicate()
            print("✗ Service konnte nicht gestartet werden")
            if stdout:
                print("STDOUT:", stdout)
            if stderr:
                print("STDERR:", stderr)
            return False
            
    except Exception as e:
        print(f"Fehler beim Starten des Service: {e}")
        return False

def main():
    """Main entry point"""
    print("=== Workflow Service Starter ===")
    
    if check_service_running():
        response = input("Service scheint bereits zu laufen. Trotzdem starten? (j/N): ")
        if response.lower() not in ('j', 'ja', 'y', 'yes'):
            print("Abgebrochen.")
            return
    
    if start_service():
        print("Service erfolgreich gestartet.")
    else:
        print("Service konnte nicht gestartet werden.")
        sys.exit(1)

if __name__ == "__main__":
    main()