#!/usr/bin/env python3
"""
demo_separated_workflow.py - Interactive demonstration of the separated workflow

This script demonstrates the file-based communication between GUI and workflow manager.
"""

import os
import sys
import time
import threading
from pathlib import Path

def simulate_gui_behavior():
    """Simulate what the GUI does when recording stops"""
    print("🎬 SIMULIERE GUI-VERHALTEN")
    print("=" * 50)
    
    print("1. Benutzer stoppt Aufnahme...")
    time.sleep(1)
    
    print("2. GUI erstellt Workflow-Trigger...")
    trigger_file = Path("workflow_trigger.txt")
    with open(trigger_file, "w") as f:
        f.write("run")
    print(f"   ✓ {trigger_file} erstellt")
    
    print("3. GUI überwacht Status-Log...")
    return True

def monitor_status_log():
    """Monitor the workflow status log like the GUI does"""
    print("\n📊 STATUS-LOG ÜBERWACHUNG")
    print("=" * 50)
    
    status_log = Path("workflow_status.log")
    last_size = 0
    max_wait = 30  # seconds
    waited = 0
    
    while waited < max_wait:
        if status_log.exists():
            current_size = status_log.stat().st_size
            if current_size > last_size:
                # New content added
                with open(status_log, "r") as f:
                    f.seek(last_size)
                    new_content = f.read()
                
                for line in new_content.strip().split('\n'):
                    if line.strip():
                        print(f"   📝 {line.strip()}")
                
                last_size = current_size
                
                # Check for completion
                if "WORKFLOW_COMPLETE" in new_content or "WORKFLOW_ERROR" in new_content:
                    print("   🎉 Workflow abgeschlossen!")
                    break
        
        time.sleep(0.5)
        waited += 0.5
    
    if waited >= max_wait:
        print("   ⏰ Timeout erreicht")
        return False
    
    return True

def start_workflow_manager():
    """Start the workflow manager in background"""
    print("\n🔄 WORKFLOW-MANAGER")
    print("=" * 50)
    
    from PythonServer import WorkflowFileWatcher
    
    watcher = WorkflowFileWatcher()
    watcher.start_watching()
    
    print(f"✓ Workflow-Manager gestartet")
    print(f"  Überwacht: {watcher.trigger_file}")
    print(f"  Loggt in: {watcher.status_log}")
    
    return watcher

def cleanup():
    """Clean up demo files"""
    files_to_clean = [
        "workflow_trigger.txt",
        "workflow_status.log",
        "transkript.txt"
    ]
    
    for filename in files_to_clean:
        file_path = Path(filename)
        if file_path.exists():
            try:
                file_path.unlink()
            except:
                pass

def main():
    """Run the separated workflow demonstration"""
    print("🚀 SEPARATED WORKFLOW DEMONSTRATION")
    print("=" * 60)
    print("Diese Demo zeigt die datei-basierte Kommunikation zwischen")
    print("GUI und Workflow-Manager (Variante 3)")
    print("=" * 60)
    
    try:
        # Clean up any existing files
        cleanup()
        
        # Step 1: Start workflow manager
        watcher = start_workflow_manager()
        
        # Give it a moment to initialize
        time.sleep(1)
        
        # Step 2: Simulate GUI creating trigger
        simulate_gui_behavior() 
        
        # Step 3: Monitor status log (like GUI does)
        success = monitor_status_log()
        
        # Step 4: Stop workflow manager
        watcher.stop_watching()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DEMO ERGEBNIS")
        print("=" * 60)
        
        if success:
            print("🎉 DEMO ERFOLGREICH!")
            print("   ✓ Trigger-Datei Mechanismus funktioniert")
            print("   ✓ Workflow-Manager reagiert automatisch")
            print("   ✓ Status-Logging funktioniert")
            print("   ✓ GUI kann Status überwachen")
            print("\n💡 Die getrennte Workflow-Architektur ist einsatzbereit!")
        else:
            print("⚠️  DEMO TEILWEISE ERFOLGREICH")
            print("   Einige Aspekte funktionieren möglicherweise nicht perfekt")
        
        print("\n📁 Generierte Dateien:")
        
        # Show generated files
        generated_files = [
            "BilderVertex/bild_*.png",
            "Transkripte/transkript*.txt", 
            "workflow_status.log"
        ]
        
        import glob
        for pattern in generated_files:
            matches = glob.glob(pattern)
            if matches:
                for match in matches[-3:]:  # Show last 3 matches
                    print(f"   📄 {match}")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n⛔ Demo durch Benutzer abgebrochen")
        return False
    except Exception as e:
        print(f"\n\n❌ Demo Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Ensure cleanup
        try:
            if 'watcher' in locals():
                watcher.stop_watching()
        except:
            pass

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + "=" * 60)
        if success:
            print("Zum Testen mit echter GUI: python3 main.py")
            print("Zum Starten des Services: python3 PythonServer.py --service")
        print("Alle Tests ausführen: python3 test_separated_workflow.py")
        print("=" * 60)
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nDemo beendet.")
        sys.exit(1)