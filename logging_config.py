#!/usr/bin/env python3
"""
logging_config.py - Unified logging configuration for all project scripts

This module provides a standardized logging setup that logs to both console
and a central 'projekt.log' file. All scripts in the project should use this
logging configuration for consistency.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime


def setup_project_logging(script_name=None, log_level=logging.INFO):
    """
    Setup unified logging for the project with both file and console output.
    
    Args:
        script_name (str, optional): Name of the script for logging context
        log_level (int, optional): Logging level (default: INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Determine script name if not provided
    if script_name is None:
        script_name = Path(sys.argv[0]).stem if sys.argv else "unknown_script"
    
    # Use standardized base directory, but fall back to current directory if not accessible
    try:
        # Primary location for Raspberry Pi deployment
        log_dir = Path("/home/pi/Desktop/v2_Tripple S")
        log_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        try:
            # Fallback to repository directory for development/testing
            log_dir = Path(__file__).parent
        except (PermissionError, OSError):
            # Last resort: current working directory
            log_dir = Path.cwd()
    
    log_file = log_dir / "projekt.log"
    
    # Create logger with script-specific name
    logger = logging.getLogger(script_name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(name)s: %(message)s'
    )
    
    # File handler - append to projekt.log
    try:
        file_handler = logging.FileHandler(str(log_file), mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # If we can't write to file, at least log to console
        print(f"Warning: Could not create log file {log_file}: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Log the initialization
    logger.info(f"=== {script_name.upper()} STARTED ===")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Working directory: {Path.cwd()}")
    logger.info(f"Script path: {Path(sys.argv[0]).absolute() if sys.argv else 'Unknown'}")
    
    return logger


def log_function_entry(logger, func_name, **kwargs):
    """
    Log function entry with parameters.
    
    Args:
        logger: Logger instance
        func_name (str): Name of the function
        **kwargs: Function parameters to log
    """
    params_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"Entering {func_name}({params_str})")


def log_function_exit(logger, func_name, result=None, error=None):
    """
    Log function exit with result or error.
    
    Args:
        logger: Logger instance
        func_name (str): Name of the function
        result: Return value (optional)
        error: Exception if function failed (optional)
    """
    if error:
        logger.error(f"Exiting {func_name} with error: {error}")
    else:
        result_str = f" -> {result}" if result is not None else ""
        logger.debug(f"Exiting {func_name}{result_str}")


def log_exception(logger, func_name, exception, reraise=True):
    """
    Log exception with full traceback.
    
    Args:
        logger: Logger instance
        func_name (str): Name of the function where exception occurred
        exception: The exception object
        reraise (bool): Whether to re-raise the exception after logging
    """
    logger.exception(f"Exception in {func_name}: {exception}")
    if reraise:
        raise exception


# Module-level convenience functions
def get_project_logger(script_name=None):
    """Get a project logger instance with standard configuration."""
    return setup_project_logging(script_name)


def setup_debug_logging(script_name=None):
    """Setup project logging with DEBUG level."""
    return setup_project_logging(script_name, log_level=logging.DEBUG)


if __name__ == "__main__":
    # Test the logging configuration
    test_logger = setup_project_logging("logging_config_test")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.debug("This is a debug message (may not be visible)")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        log_exception(test_logger, "test_function", e, reraise=False)
    
    test_logger.info("Logging configuration test completed")