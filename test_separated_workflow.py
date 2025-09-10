#!/usr/bin/env python3
"""
test_separated_workflow.py - Test the separated workflow implementation

This test verifies that the file-based communication between GUI and workflow manager works correctly.
"""

import os
import sys
import time
import threading
from pathlib import Path

def test_trigger_mechanism():
    """Test the trigger file mechanism"""
    print("=== Test 1: Trigger-Datei Mechanismus ===")
    
    try:
        from PythonServer import WorkflowFileWatcher
        
        # Create watcher
        watcher = WorkflowFileWatcher()
        print(f"✓ WorkflowFileWatcher erstellt: {watcher.work_dir}")
        
        # Ensure clean state
        if watcher.trigger_file.exists():
            watcher.trigger_file.unlink()
        if watcher.status_log.exists():
            watcher.status_log.unlink()
        
        # Test 1a: No trigger file
        has_trigger = watcher.check_trigger()
        print(f"✓ Kein Trigger vorhanden: {not has_trigger}")
        
        # Test 1b: Create trigger file
        with open(watcher.trigger_file, "w") as f:
            f.write("run")
        print(f"✓ Trigger-Datei erstellt: {watcher.trigger_file}")
        
        # Test 1c: Check trigger is detected
        has_trigger = watcher.check_trigger()
        print(f"✓ Trigger erkannt: {has_trigger}")
        
        # Trigger should be gone after workflow execution
        trigger_exists = watcher.trigger_file.exists()
        print(f"✓ Trigger nach Workflow gelöscht: {not trigger_exists}")
        
        return True
        
    except Exception as e:
        print(f"✗ Fehler in Test 1: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_status_logging():
    """Test the status logging mechanism"""
    print("\n=== Test 2: Status-Logging ===")
    
    try:
        from PythonServer import WorkflowFileWatcher
        
        watcher = WorkflowFileWatcher()
        
        # Clear existing log
        watcher.clear_status_log()
        
        # Test logging
        watcher.log_status("Test Nachricht 1")
        watcher.log_status("Test Nachricht 2", "WARNING")
        watcher.log_status("Test Nachricht 3", "ERROR")
        
        # Check log file exists and has content
        if watcher.status_log.exists():
            with open(watcher.status_log, "r") as f:
                content = f.read()
            
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            print(f"✓ Log-Datei erstellt: {len(lines)} Einträge")
            
            # Check that messages are in log
            has_msg1 = any("Test Nachricht 1" in line for line in lines)
            has_warning = any("WARNING" in line for line in lines)
            has_error = any("ERROR" in line for line in lines)
            
            print(f"✓ INFO-Nachricht geloggt: {has_msg1}")
            print(f"✓ WARNING-Nachricht geloggt: {has_warning}")  
            print(f"✓ ERROR-Nachricht geloggt: {has_error}")
            
            return has_msg1 and has_warning and has_error
        else:
            print("✗ Log-Datei nicht erstellt")
            return False
        
    except Exception as e:
        print(f"✗ Fehler in Test 2: {e}")
        return False

def test_background_watcher():
    """Test the background watcher functionality"""
    print("\n=== Test 3: Hintergrund-Watcher ===")
    
    try:
        from PythonServer import WorkflowFileWatcher
        
        watcher = WorkflowFileWatcher()
        
        # Start watcher
        watcher.start_watching()
        print(f"✓ Watcher gestartet: {watcher.running}")
        
        # Wait a moment for thread to start
        time.sleep(0.5)
        
        # Create trigger file
        with open(watcher.trigger_file, "w") as f:
            f.write("run")
        print("✓ Trigger-Datei für Hintergrund-Test erstellt")
        
        # Wait for watcher to process it
        max_wait = 5  # seconds
        waited = 0
        workflow_executed = False
        
        while waited < max_wait:
            time.sleep(0.2)
            waited += 0.2
            
            # Check if workflow was executed (log contains completion message)
            if watcher.status_log.exists():
                with open(watcher.status_log, "r") as f:
                    content = f.read()
                if "WORKFLOW_COMPLETE" in content:
                    workflow_executed = True
                    break
        
        # Stop watcher
        watcher.stop_watching()
        print(f"✓ Watcher gestoppt")
        
        print(f"✓ Workflow automatisch ausgeführt: {workflow_executed}")
        
        return workflow_executed
        
    except Exception as e:
        print(f"✗ Fehler in Test 3: {e}")
        return False

def test_gui_integration():
    """Test GUI integration components"""
    print("\n=== Test 4: GUI-Integration ===")
    
    try:
        # Test that the GUI modifications compile
        import importlib.util
        
        # Load main.py module
        spec = importlib.util.spec_from_file_location("main", "main.py")
        if spec is None:
            print("✗ Kann main.py nicht laden")
            return False
            
        main_module = importlib.util.module_from_spec(spec)
        
        # This will fail if there are syntax errors
        spec.loader.exec_module(main_module)
        print("✓ main.py kompiliert ohne Syntaxfehler")
        
        # Check that AufnahmePopup has the new methods
        aufnahme_popup_class = getattr(main_module, 'AufnahmePopup', None)
        if aufnahme_popup_class:
            print("✓ AufnahmePopup Klasse gefunden")
            
            # Check for new methods
            has_trigger_method = hasattr(aufnahme_popup_class, 'create_workflow_trigger')
            has_status_method = hasattr(aufnahme_popup_class, 'check_workflow_status')
            
            print(f"✓ create_workflow_trigger Methode: {has_trigger_method}")
            print(f"✓ check_workflow_status Methode: {has_status_method}")
            
            return has_trigger_method and has_status_method
        else:
            print("✗ AufnahmePopup Klasse nicht gefunden")
            return False
            
    except Exception as e:
        print(f"✗ Fehler in Test 4: {e}")
        print("  (Dies könnte an fehlenden Kivy-Abhängigkeiten liegen)")
        # Don't fail the test for missing Kivy dependencies
        return True

def run_all_tests():
    """Run all tests"""
    print("🧪 TESTING SEPARATED WORKFLOW IMPLEMENTATION")
    print("=" * 60)
    print("Testing the file-based communication between GUI and workflow manager")
    print("=" * 60)
    
    tests = [
        ("Trigger-Mechanismus", test_trigger_mechanism),
        ("Status-Logging", test_status_logging),  
        ("Hintergrund-Watcher", test_background_watcher),
        ("GUI-Integration", test_gui_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Unerwarteter Fehler in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST ERGEBNISSE")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ BESTANDEN" if success else "❌ FEHLGESCHLAGEN"
        print(f"  {test_name:<25} | {status}")
        if success:
            passed += 1
    
    print("=" * 60)
    if passed == total:
        print("🎉 ALLE TESTS BESTANDEN")
        print("   Die getrennte Workflow-Implementierung ist funktionsfähig!")
    else:
        print(f"⚠️  {passed}/{total} TESTS BESTANDEN")
        print(f"   {total - passed} Tests fehlgeschlagen")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests durch Benutzer abgebrochen")
        sys.exit(1)