#!/usr/bin/env python3
"""
programmSendFile.py - File transmission and upload script

This script handles sending files to remote servers, managing uploads,
and coordinating file transfers within the project workflow.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
from logging_config import setup_project_logging, log_function_entry, log_function_exit, log_exception

# Setup project logging
logger = setup_project_logging("programmSendFile")

# Configuration
BASE_DIR = Path("/home/pi/Desktop/v2_Tripple S")
UPLOAD_LOG_FILE = "upload.log"
CONFIG_FILE = "upload_config.json"

# Default upload configuration
DEFAULT_CONFIG = {
    "server_host": "example.com",
    "server_port": 22,
    "username": "user",
    "upload_path": "/home/user/uploads/",
    "use_ssh_key": True,
    "ssh_key_path": "~/.ssh/id_rsa",
    "timeout": 30,
    "retry_count": 3
}


def load_upload_config(config_path=None):
    """
    Load upload configuration from JSON file.
    
    Args:
        config_path (str|Path, optional): Path to config file
    
    Returns:
        dict: Upload configuration
    """
    log_function_entry(logger, "load_upload_config", config_path=str(config_path) if config_path else None)
    
    if config_path is None:
        work_dir = BASE_DIR if BASE_DIR.exists() else Path.cwd()
        config_path = work_dir / CONFIG_FILE
    else:
        config_path = Path(config_path)
    
    try:
        if config_path.exists():
            logger.info(f"Loading upload configuration from: {config_path}")
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Merge with defaults for missing keys
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
                    logger.debug(f"Added default config value: {key} = {value}")
            
            logger.info("Upload configuration loaded successfully")
            log_function_exit(logger, "load_upload_config", result=True)
            return config
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            logger.info("Creating default config file...")
            save_upload_config(DEFAULT_CONFIG, config_path)
            log_function_exit(logger, "load_upload_config", result="default")
            return DEFAULT_CONFIG.copy()
            
    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults")
        log_exception(logger, "load_upload_config", e, reraise=False)
        return DEFAULT_CONFIG.copy()


def save_upload_config(config, config_path=None):
    """
    Save upload configuration to JSON file.
    
    Args:
        config (dict): Configuration to save
        config_path (str|Path, optional): Path to config file
    
    Returns:
        bool: True if successful, False otherwise
    """
    log_function_entry(logger, "save_upload_config", config_keys=list(config.keys()))
    
    if config_path is None:
        work_dir = BASE_DIR if BASE_DIR.exists() else Path.cwd()
        config_path = work_dir / CONFIG_FILE
    else:
        config_path = Path(config_path)
    
    try:
        logger.info(f"Saving upload configuration to: {config_path}")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info("Upload configuration saved successfully")
        log_function_exit(logger, "save_upload_config", result=True)
        return True
        
    except Exception as e:
        log_exception(logger, "save_upload_config", e, reraise=False)
        return False


def upload_file_ssh(file_path, config, remote_filename=None):
    """
    Upload file via SSH/SCP.
    
    Args:
        file_path (str|Path): Local file path to upload
        config (dict): Upload configuration
        remote_filename (str, optional): Remote filename (defaults to local filename)
    
    Returns:
        dict: Upload result with status and details
    """
    log_function_entry(logger, "upload_file_ssh", file_path=str(file_path), remote_filename=remote_filename)
    
    file_path = Path(file_path)
    result = {
        "success": False,
        "error": None,
        "upload_time": None,
        "file_size": 0,
        "remote_path": None
    }
    
    try:
        if not file_path.exists():
            error_msg = f"File does not exist: {file_path}"
            logger.error(error_msg)
            result["error"] = error_msg
            log_function_exit(logger, "upload_file_ssh", error=error_msg)
            return result
        
        # Get file info
        file_size = file_path.stat().st_size
        result["file_size"] = file_size
        logger.info(f"Uploading file: {file_path} ({file_size:,} bytes)")
        
        # Determine remote filename and path
        if remote_filename is None:
            remote_filename = file_path.name
        
        remote_path = f"{config['upload_path']}/{remote_filename}"
        result["remote_path"] = remote_path
        logger.debug(f"Remote path: {remote_path}")
        
        # Build SCP command
        host_spec = f"{config['username']}@{config['server_host']}"
        if config.get('use_ssh_key', True) and config.get('ssh_key_path'):
            ssh_key_path = os.path.expanduser(config['ssh_key_path'])
            cmd = [
                'scp',
                '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', f"ConnectTimeout={config.get('timeout', 30)}",
                str(file_path),
                f"{host_spec}:{remote_path}"
            ]
        else:
            cmd = [
                'scp',
                '-o', 'StrictHostKeyChecking=no',
                '-o', f"ConnectTimeout={config.get('timeout', 30)}",
                str(file_path),
                f"{host_spec}:{remote_path}"
            ]
        
        logger.info(f"Running SCP command: {' '.join(cmd[:3])} [credentials hidden]")
        
        # Execute upload with retries
        retry_count = config.get('retry_count', 3)
        last_error = None
        
        for attempt in range(1, retry_count + 1):
            logger.info(f"Upload attempt {attempt}/{retry_count}")
            
            try:
                start_time = time.time()
                process_result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=config.get('timeout', 30) * 2  # Give extra time for large files
                )
                end_time = time.time()
                upload_duration = end_time - start_time
                
                if process_result.returncode == 0:
                    logger.info(f"Upload successful in {upload_duration:.2f} seconds")
                    result["success"] = True
                    result["upload_time"] = upload_duration
                    log_function_exit(logger, "upload_file_ssh", result=True)
                    return result
                else:
                    error_msg = f"SCP failed (exit code {process_result.returncode}): {process_result.stderr}"
                    logger.warning(f"Attempt {attempt} failed: {error_msg}")
                    last_error = error_msg
                    
                    if attempt < retry_count:
                        wait_time = attempt * 2  # Exponential backoff
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    
            except subprocess.TimeoutExpired:
                error_msg = f"Upload timeout after {config.get('timeout', 30) * 2} seconds"
                logger.warning(f"Attempt {attempt} timed out")
                last_error = error_msg
                
                if attempt < retry_count:
                    wait_time = attempt * 2
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
        
        # All attempts failed
        result["error"] = f"Upload failed after {retry_count} attempts. Last error: {last_error}"
        logger.error(result["error"])
        log_function_exit(logger, "upload_file_ssh", error=result["error"])
        return result
        
    except Exception as e:
        result["error"] = str(e)
        log_exception(logger, "upload_file_ssh", e, reraise=False)
        return result


def upload_transcript_files(config=None):
    """
    Upload transcript files to remote server.
    
    Args:
        config (dict, optional): Upload configuration
    
    Returns:
        dict: Upload results for each file
    """
    log_function_entry(logger, "upload_transcript_files")
    
    if config is None:
        config = load_upload_config()
    
    # Determine working directory
    work_dir = BASE_DIR if BASE_DIR.exists() else Path.cwd()
    logger.info(f"Looking for transcript files in: {work_dir}")
    
    # Files to upload
    files_to_upload = [
        "transkript.txt",
        "transkript.json"
    ]
    
    results = {}
    
    for filename in files_to_upload:
        file_path = work_dir / filename
        
        if file_path.exists():
            logger.info(f"Uploading: {filename}")
            result = upload_file_ssh(file_path, config)
            results[filename] = result
            
            if result["success"]:
                logger.info(f"✓ {filename} uploaded successfully")
                print(f"✓ {filename} uploaded successfully")
            else:
                logger.error(f"✗ {filename} upload failed: {result['error']}")
                print(f"✗ {filename} upload failed: {result['error']}")
        else:
            logger.warning(f"File not found, skipping: {filename}")
            print(f"⚠ File not found, skipping: {filename}")
            results[filename] = {
                "success": False,
                "error": "File not found",
                "skipped": True
            }
    
    log_function_exit(logger, "upload_transcript_files", result=len([r for r in results.values() if r["success"]]))
    return results


def check_connection(config=None):
    """
    Test connection to remote server.
    
    Args:
        config (dict, optional): Upload configuration
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    log_function_entry(logger, "check_connection")
    
    if config is None:
        config = load_upload_config()
    
    try:
        logger.info(f"Testing connection to {config['server_host']}:{config.get('server_port', 22)}")
        
        host_spec = f"{config['username']}@{config['server_host']}"
        
        if config.get('use_ssh_key', True) and config.get('ssh_key_path'):
            ssh_key_path = os.path.expanduser(config['ssh_key_path'])
            cmd = [
                'ssh',
                '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'BatchMode=yes',
                '-o', f"ConnectTimeout={config.get('timeout', 30)}",
                host_spec,
                'echo "Connection test successful"'
            ]
        else:
            cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'BatchMode=yes',
                '-o', f"ConnectTimeout={config.get('timeout', 30)}",
                host_spec,
                'echo "Connection test successful"'
            ]
        
        logger.debug("Running SSH connection test...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.get('timeout', 30)
        )
        
        if result.returncode == 0:
            logger.info("Connection test successful")
            log_function_exit(logger, "check_connection", result=True)
            return True
        else:
            logger.error(f"Connection test failed: {result.stderr}")
            log_function_exit(logger, "check_connection", error=result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Connection test timed out")
        log_function_exit(logger, "check_connection", error="Timeout")
        return False
    except Exception as e:
        log_exception(logger, "check_connection", e, reraise=False)
        return False


def main():
    """Main entry point for file upload operations"""
    log_function_entry(logger, "main")
    logger.info("Starting file upload workflow")
    
    try:
        # Load configuration
        logger.info("Step 1: Loading upload configuration...")
        config = load_upload_config()
        
        print("=== File Upload Service ===")
        print(f"Server: {config['server_host']}")
        print(f"Username: {config['username']}")
        print(f"Upload path: {config['upload_path']}")
        
        # Test connection
        logger.info("Step 2: Testing server connection...")
        if check_connection(config):
            logger.info("✓ Server connection successful")
            print("✓ Server connection successful")
        else:
            logger.warning("⚠ Server connection failed - uploads may not work")
            print("⚠ Server connection failed - uploads may not work")
        
        # Upload transcript files
        logger.info("Step 3: Uploading transcript files...")
        results = upload_transcript_files(config)
        
        # Summary
        successful_uploads = [f for f, r in results.items() if r["success"]]
        failed_uploads = [f for f, r in results.items() if not r["success"] and not r.get("skipped")]
        
        logger.info(f"Upload summary: {len(successful_uploads)} successful, {len(failed_uploads)} failed")
        print(f"\nUpload Summary:")
        print(f"  Successful: {len(successful_uploads)}")
        print(f"  Failed: {len(failed_uploads)}")
        
        if successful_uploads:
            print("  ✓ Successfully uploaded:")
            for filename in successful_uploads:
                print(f"    - {filename}")
        
        if failed_uploads:
            print("  ✗ Failed uploads:")
            for filename in failed_uploads:
                print(f"    - {filename}: {results[filename]['error']}")
        
        logger.info("File upload workflow completed")
        log_function_exit(logger, "main", result=len(successful_uploads) > 0)
        
    except Exception as e:
        log_exception(logger, "main", e, reraise=False)


if __name__ == "__main__":
    main()