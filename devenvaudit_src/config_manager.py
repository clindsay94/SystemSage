"""
Manages loading from and saving to 'devenvaudit_config.json'.
Handles user-defined scan paths, inclusion/exclusion patterns,
the persistent ignore list, and user preferences for package managers.
"""
import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Define the name for the configuration file
CONFIG_FILE_NAME = "devenvaudit_config.json"

# Path for the configuration file within the devenvaudit_src directory
CONFIG_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, CONFIG_FILE_NAME)


DEFAULT_CONFIG: Dict[str, Any] = {
    "scan_options": {
        "scan_paths": ["~"],  # Default to user's home directory
        "excluded_paths": [
            "~/Library", "/System", "/private", "/var/log", "/tmp",
            "C:\\Windows", "C:\\Program Files (x86)\\Common Files", "C:\\Program
Data\\Package Cache" # Common noisy/system paths
        ],
        "scan_env_vars": True,
        "cross_reference_tools": True, # e.g., check if JAVA_HOME points to a de
tected Java
        "perform_update_checks": True, # Check for updates using package manager
s
        "preferred_package_managers_windows": ["winget", "choco", "scoop"],
        "preferred_package_managers_linux": ["apt", "dnf", "yum", "pacman", "sna
p", "flatpak"],
        "preferred_package_managers_darwin": ["brew"],
        "executable_extensions": ['.exe', '.bat', '.cmd', '.sh', '.py', '.jar',
'.msi', '.dmg', '.pkg'] # Added more
    },
    "logging": {
        "level": "INFO", # DEBUG, INFO, WARNING, ERROR, CRITICAL
        "file": "devenvaudit.log" # Log file name (will be placed in CONFIG_DIR_
PATH)
    },
    "ignored_tools_identifiers": [], # List of component IDs to ignore in report
s
    "user_preferences": {
        "theme": "default",
        "always_show_details": False
    }
}

def _ensure_config_dir_exists():
    """Ensures the configuration directory exists. Creates it if not."""
    # This function might still be useful if the config directory is elsewhere,
    # but for a local config file, it's less critical if the parent dir (devenvaudit_src) is assumed to exist.
    # For now, we'll keep it, but its necessity changes with CONFIG_DIR_PATH.
    if not os.path.exists(CONFIG_DIR_PATH) and CONFIG_DIR_PATH != os.path.dirname(os.path.abspath(__file__)):
        # Only create if CONFIG_DIR_PATH is not the script's own directory.
        try:
            os.makedirs(CONFIG_DIR_PATH)
            logger.info(f"Created configuration directory: {CONFIG_DIR_PATH}")
        except OSError as e:
            logger.error(f"Could not create configuration directory {CONFIG_DIR_PATH}: {e}")


def load_config() -> Dict[str, Any]:
    """
    Reads 'devenvaudit_config.json', returns a dictionary of settings.
    Handles file not found by returning defaults and creating the file.
    Handles JSON decode errors by returning defaults and attempting to backup/ov
erwrite.
    """
    # _ensure_config_dir_exists() # Called by save_config if file not found, or can be called explicitly if needed.

    if not os.path.exists(CONFIG_FILE_PATH):
        logger.warning(f"Configuration file not found at {CONFIG_FILE_PATH}. Creating with default settings.")
        save_config(DEFAULT_CONFIG) # Save defaults if file doesn't exist
        return DEFAULT_CONFIG.copy() # Return a copy of defaults

    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            loaded_settings = json.load(f)
            # TODO: Add schema validation or migration logic here if config stru
cture changes
            logger.info(f"Configuration loaded successfully from {CONFIG_FILE_PA
TH}")
            return loaded_settings
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {CONFIG_FILE_PATH}: {e}. Backing
 up and using default settings.")
        backup_path = CONFIG_FILE_PATH + ".corrupt_backup"
        try:
            os.rename(CONFIG_FILE_PATH, backup_path)
            logger.info(f"Backed up corrupted config to {backup_path}")
        except OSError as backup_e:
            logger.error(f"Could not backup corrupted config file: {backup_e}")

        save_config(DEFAULT_CONFIG) # Save defaults to overwrite corrupted file
        return DEFAULT_CONFIG.copy()
    except Exception as e: # Catch other potential errors during file read
        logger.error(f"Failed to load configuration from {CONFIG_FILE_PATH} due
to an unexpected error: {e}. Using default settings.", exc_info=True)
        return DEFAULT_CONFIG.copy()


def save_config(settings_dict: Dict[str, Any]) -> bool:
    """
    Writes the settings dictionary to 'devenvaudit_config.json'.

    Args:
        settings_dict (dict): The configuration dictionary to save.

    Returns:
        bool: True if save was successful, False otherwise.
    """
    _ensure_config_dir_exists() # Ensure dir exists, especially if it's not the script's own dir.

    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=4)
        logger.info(f"Configuration saved successfully to {CONFIG_FILE_PATH}")
        return True
    except IOError as e:
        logger.error(f"Could not write configuration to {CONFIG_FILE_PATH}: {e}"
)
        return False
    except TypeError as e: # e.g. if settings_dict is not JSON serializable
        logger.error(f"Configuration data is not serializable (TypeError): {e}")
        return False

def get_scan_options() -> Dict[str, Any]:
    """Convenience function to get just the 'scan_options' part of the config.""
"
    config = load_config()
    return config.get("scan_options", DEFAULT_CONFIG["scan_options"])

def get_ignored_identifiers() -> List[str]:
    """Convenience function to get the list of ignored tool identifiers."""
    config = load_config()
    return config.get("ignored_tools_identifiers", DEFAULT_CONFIG["ignored_tools
_identifiers"])

def add_to_ignored_identifiers(identifier: str):
    """Adds a tool identifier to the ignored list and saves the config."""
    config = load_config()
    if "ignored_tools_identifiers" not in config:
        config["ignored_tools_identifiers"] = []

    if identifier not in config["ignored_tools_identifiers"]:
        config["ignored_tools_identifiers"].append(identifier)
        save_config(config)
        logger.info(f"Added '{identifier}' to ignored tools list.")
    else:
        logger.info(f"'{identifier}' is already in the ignored tools list.")

def remove_from_ignored_identifiers(identifier: str):
    """Removes a tool identifier from the ignored list and saves the config."""
    config = load_config()
    if "ignored_tools_identifiers" in config and identifier in config["ignored_t
ools_identifiers"]:
        config["ignored_tools_identifiers"].remove(identifier)
        save_config(config)
        logger.info(f"Removed '{identifier}' from ignored tools list.")
    else:
        logger.warning(f"'{identifier}' not found in the ignored tools list.")

# Example of how to use it (optional, for direct testing of this module)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG) # Set to DEBUG for detailed output
from this module

    print(f"Config file will be managed at: {CONFIG_FILE_PATH}")

    # Ensure directory exists for the test (if it's not the script's own directory)
    _ensure_config_dir_exists()

    # Test loading (will create default if not exists)
    current_settings = load_config()
    print("\nInitial or Loaded Settings:")
    print(json.dumps(current_settings, indent=4))

    # Test modifying and saving
    current_settings["user_preferences"]["theme"] = "dark_custom"
    current_settings["scan_options"]["perform_update_checks"] = False
    if save_config(current_settings):
        print("\nModified settings saved.")

        # Test reloading
        reloaded_settings = load_config()
        print("\nReloaded Settings:")
        print(json.dumps(reloaded_settings, indent=4))

        # Verify changes
        assert reloaded_settings["user_preferences"]["theme"] == "dark_custom"
        assert not reloaded_settings["scan_options"]["perform_update_checks"]
    else:
        print("\nFailed to save modified settings.")

    # Test scan options retrieval
    scan_opts = get_scan_options()
    print("\nScan Options:")
    print(json.dumps(scan_opts, indent=4))

    # Test ignored identifiers
    print("\nTesting ignored identifiers:")
    add_to_ignored_identifiers("python_3.9_system")
    add_to_ignored_identifiers("vscode_1.80_user")
    add_to_ignored_identifiers("python_3.9_system") # Test adding duplicate
    print(f"Current ignored list: {get_ignored_identifiers()}")
    remove_from_ignored_identifiers("vscode_1.80_user")
    remove_from_ignored_identifiers("non_existent_tool") # Test removing non-exi
stent
    print(f"Final ignored list: {get_ignored_identifiers()}")

    # Test with a potentially corrupted file (manual step: corrupt the JSON file
, then run)
    # print("\nTesting resilience against corrupted config (manual step needed).
..")
    # Manually corrupt devenvaudit_config.json here, then uncomment and run the
load_config() below
    # corrupted_settings = load_config()
    # print("Settings after attempting to load corrupted file:")
    # print(json.dumps(corrupted_settings, indent=4))
    # assert corrupted_settings["user_preferences"]["theme"] == DEFAULT_CONFIG["
user_preferences"]["theme"] # Should revert to default
    print("\nConfig manager tests complete.")
