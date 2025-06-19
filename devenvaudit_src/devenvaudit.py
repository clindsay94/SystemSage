"""
Developer Environment Auditor (DevEnvAudit)

This module provides the core logic for auditing the developer environment.
It is intended to be imported and used by the main SystemSage application.
"""

import logging
import os


from config_manager import CONFIG_FILE_PATH
from devenvaudit_src.scan_logic import (
    EnvironmentScanner,
)  # Ensure this import is correct

# --- Global Constants ---
APP_NAME = "Developer Environment Auditor"
APP_VERSION = "1.1.0"  # Corresponds to prompt version
LOG_FILE_NAME = "devenvaudit_module.log"  # Renamed to reflect its module role


def setup_logging():
    """Configures logging for the module if run standalone,
    or if the main app doesn't set up logging globally.
    Consider removing or adapting if SystemSageV2.0.py has primary logging setup.
    """
    log_dir = os.path.dirname(CONFIG_FILE_PATH)  # Place log file near config file
    log_file = os.path.join(log_dir, LOG_FILE_NAME)

    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            print(
                f"Warning: Could not create log directory {log_dir}: {e}. Logging to current directory."
            )
            log_file = LOG_FILE_NAME

    logging.basicConfig(
        level=logging.INFO,  # Default level for file and console
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, mode="a", encoding="utf-8"),  # Append
            logging.StreamHandler(),  # Outputs to console (stderr by default)
        ],
    )
    logging.info(
        f"{APP_NAME} v{APP_VERSION} module logging initialized. Log file: {log_file}"
    )


# --- Functions that the main SystemSageApp would call ---


def get_devenvaudit_results(progress_callback=None, status_callback=None):
    """
    Performs the developer environment audit and returns the results.
    This function is designed to be called by the main SystemSage application.
    """
    # Assuming EnvironmentScanner is what actually performs the scan
    scanner = EnvironmentScanner(
        progress_callback=progress_callback, status_callback=status_callback
    )
    components, env_vars, issues = scanner.run_scan()
    return components, env_vars, issues


