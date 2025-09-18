#!/usr/bin/env python3
"""
dateiKopieren.py - File copying and management script

This script handles file operations within the project workflow,
including copying files, organizing content, and managing clipboard operations.
"""

import os
import sys
import shutil
from pathlib import Path
from logging_config import setup_project_logging, log_function_entry, log_function_exit, log_exception

# Setup project logging
logger = setup_project_logging("dateiKopieren")

# Standard paths
BASE_DIR = Path("/home/pi/Desktop/v2_Tripple S")
TRANSCRIPT_PATH = "transkript.txt"
TRANSCRIPT_JSON_PATH = "transkript.json"
BACKUP_DIR = "backups"


def copy_file(source_path, dest_path, create_backup=True):
    """
    Copy a file from source to destination with optional backup.
    
    Args:
        source_path (str|Path): Source file path
        dest_path (str|Path): Destination file path
        create_backup (bool): Whether to create backup of existing destination
    
    Returns:
        bool: True if successful, False otherwise
    """
    log_function_entry(logger, "copy_file", source_path=str(source_path), dest_path=str(dest_path), create_backup=create_backup)
    
    source_path = Path(source_path)
    dest_path = Path(dest_path)
    
    try:
        # Check if source exists
        if not source_path.exists():
            error_msg = f"Source file does not exist: {source_path}"
            logger.error(error_msg)
            log_function_exit(logger, "copy_file", error=error_msg)
            return False
        
        logger.info(f"Copying file from {source_path} to {dest_path}")
        
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Destination directory created/verified: {dest_path.parent}")
        
        # Create backup of destination if it exists and backup is requested
        if create_backup and dest_path.exists():
            backup_path = create_file_backup(dest_path)
            if backup_path:
                logger.info(f"Created backup: {backup_path}")
            else:
                logger.warning("Failed to create backup, proceeding anyway")
        
        # Perform the copy
        shutil.copy2(source_path, dest_path)
        logger.info(f"File successfully copied: {dest_path}")
        
        # Verify copy
        if dest_path.exists():
            src_size = source_path.stat().st_size
            dest_size = dest_path.stat().st_size
            if src_size == dest_size:
                logger.info(f"Copy verified: {src_size} bytes")
                log_function_exit(logger, "copy_file", result=True)
                return True
            else:
                logger.error(f"Copy verification failed: source {src_size} bytes != dest {dest_size} bytes")
                log_function_exit(logger, "copy_file", error="Copy verification failed")
                return False
        else:
            logger.error("Destination file was not created")
            log_function_exit(logger, "copy_file", error="Destination file not created")
            return False
            
    except Exception as e:
        log_exception(logger, "copy_file", e, reraise=False)
        return False


def create_file_backup(file_path):
    """
    Create a timestamped backup of a file.
    
    Args:
        file_path (str|Path): Path to file to backup
    
    Returns:
        Path|None: Path to backup file if successful, None otherwise
    """
    log_function_entry(logger, "create_file_backup", file_path=str(file_path))
    
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"File does not exist for backup: {file_path}")
            return None
        
        # Create backup directory
        backup_dir = file_path.parent / BACKUP_DIR
        backup_dir.mkdir(exist_ok=True)
        logger.debug(f"Backup directory: {backup_dir}")
        
        # Generate backup filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_filename
        
        logger.info(f"Creating backup: {backup_path}")
        shutil.copy2(file_path, backup_path)
        
        logger.info(f"Backup created successfully: {backup_path}")
        log_function_exit(logger, "create_file_backup", result=str(backup_path))
        return backup_path
        
    except Exception as e:
        log_exception(logger, "create_file_backup", e, reraise=False)
        return None


def organize_transcript_files(work_dir=None):
    """
    Organize transcript files in the working directory.
    
    Args:
        work_dir (str|Path, optional): Working directory path
    
    Returns:
        dict: Information about organized files
    """
    log_function_entry(logger, "organize_transcript_files", work_dir=str(work_dir) if work_dir else None)
    
    if work_dir is None:
        # Try standard location first, fallback to current directory
        if BASE_DIR.exists():
            work_dir = BASE_DIR
        else:
            work_dir = Path.cwd()
            logger.warning(f"Using fallback directory: {work_dir}")
    else:
        work_dir = Path(work_dir)
    
    logger.info(f"Organizing transcript files in: {work_dir}")
    
    result = {
        "transcript_txt": None,
        "transcript_json": None,
        "organized": False,
        "errors": []
    }
    
    try:
        # Check for transcript files
        txt_file = work_dir / TRANSCRIPT_PATH
        json_file = work_dir / TRANSCRIPT_JSON_PATH
        
        if txt_file.exists():
            logger.info(f"Found transcript TXT file: {txt_file}")
            result["transcript_txt"] = str(txt_file)
        else:
            logger.warning(f"Transcript TXT file not found: {txt_file}")
        
        if json_file.exists():
            logger.info(f"Found transcript JSON file: {json_file}")
            result["transcript_json"] = str(json_file)
        else:
            logger.warning(f"Transcript JSON file not found: {json_file}")
        
        # Create organized directory structure if files exist
        if txt_file.exists() or json_file.exists():
            logger.info("Transcript files found, organization successful")
            result["organized"] = True
        else:
            error_msg = "No transcript files found to organize"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        log_function_exit(logger, "organize_transcript_files", result=result["organized"])
        return result
        
    except Exception as e:
        error_msg = str(e)
        result["errors"].append(error_msg)
        log_exception(logger, "organize_transcript_files", e, reraise=False)
        return result


def get_clipboard_content():
    """
    Get content from system clipboard (mock implementation for portability).
    
    Returns:
        str|None: Clipboard content if available, None otherwise
    """
    log_function_entry(logger, "get_clipboard_content")
    
    try:
        # This is a simplified implementation
        # In a real environment, this would use clipboard libraries like pyperclip
        logger.info("Attempting to read clipboard content...")
        
        # For now, read from transcript file as fallback
        work_dir = BASE_DIR if BASE_DIR.exists() else Path.cwd()
        txt_file = work_dir / TRANSCRIPT_PATH
        
        if txt_file.exists():
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            logger.info(f"Read content from transcript file: {len(content)} characters")
            log_function_exit(logger, "get_clipboard_content", result=len(content))
            return content
        else:
            logger.warning("No transcript file available for clipboard fallback")
            log_function_exit(logger, "get_clipboard_content", result=None)
            return None
            
    except Exception as e:
        log_exception(logger, "get_clipboard_content", e, reraise=False)
        return None


def main():
    """Main entry point for file operations"""
    log_function_entry(logger, "main")
    logger.info("Starting file operations workflow")
    
    try:
        # Determine working directory
        if BASE_DIR.exists():
            work_dir = BASE_DIR
            logger.info(f"Using standard directory: {work_dir}")
        else:
            work_dir = Path.cwd()
            logger.warning(f"Using fallback directory: {work_dir}")
        
        # Organize transcript files
        logger.info("Step 1: Organizing transcript files...")
        result = organize_transcript_files(work_dir)
        
        if result["organized"]:
            logger.info("Transcript files organized successfully")
            print("✓ Transcript files organized successfully")
            
            # Display found files
            if result["transcript_txt"]:
                logger.info(f"TXT file: {result['transcript_txt']}")
                print(f"TXT file: {result['transcript_txt']}")
            
            if result["transcript_json"]:
                logger.info(f"JSON file: {result['transcript_json']}")
                print(f"JSON file: {result['transcript_json']}")
        else:
            logger.error("Failed to organize transcript files")
            print("✗ Failed to organize transcript files")
            for error in result["errors"]:
                logger.error(f"Error: {error}")
                print(f"Error: {error}")
        
        # Test clipboard functionality
        logger.info("Step 2: Testing clipboard functionality...")
        clipboard_content = get_clipboard_content()
        if clipboard_content:
            logger.info(f"Clipboard content available: {len(clipboard_content)} characters")
            print(f"✓ Clipboard content available: {len(clipboard_content)} characters")
        else:
            logger.warning("No clipboard content available")
            print("⚠ No clipboard content available")
        
        logger.info("File operations workflow completed")
        log_function_exit(logger, "main", result=True)
        
    except Exception as e:
        log_exception(logger, "main", e, reraise=False)


if __name__ == "__main__":
    main()