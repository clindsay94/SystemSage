# Overclocker's Logbook (OCL) Module - Architecture & API

This document outlines the identified Python structure and API of the Overclocker's Logbook (OCL) module, intended for integration with the SystemSage PC application.

## Repository Structure Overview

The OCL module is located at `https://github.com/clindsay94/Overclockers-Logbook` (branch `feature/system-sage-refactor`). While the repository also contains code for a web frontend (TypeScript/HTML), the Python components relevant to SystemSage PC integration are primarily within the `system_sage_core/` subdirectory.

## Python Module: `system_sage_core`

This directory is structured as a Python package. It contains the data models, database interaction logic, and the public API for managing overclocking profiles. The data is stored in an SQLite database (`system_sage_olb.db`) within this directory.

### Key Python Files:

*   **`system_sage_core/olb_api.py`**: Defines the public functions SystemSage should use to interact with the OCL module.
*   **`system_sage_core/database.py`**: Handles all SQLite database operations (schema definition, CRUD functions for profiles, settings, and logs). It creates and uses `system_sage_olb.db`.
*   **`system_sage_core/profiles.py`**: Defines the `Profile` and `SettingsCategory` data model classes (though `SettingsCategory` is not directly used by the current API functions, settings are stored with a `category` string).

### Database Schema (`system_sage_olb.db` via `database.py`):

*   **`profiles` table:**
    *   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    *   `name` (TEXT NOT NULL)
    *   `description` (TEXT)
    *   `creation_date` (TEXT NOT NULL, ISO format)
    *   `last_modified_date` (TEXT NOT NULL, ISO format)
*   **`settings` table:**
    *   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    *   `profile_id` (INTEGER NOT NULL, FOREIGN KEY to `profiles.id` ON DELETE CASCADE)
    *   `category` (TEXT NOT NULL)
    *   `setting_name` (TEXT NOT NULL)
    *   `setting_value` (TEXT)
    *   `value_type` (TEXT) - e.g., "str", "int", "float", "bool"
    *   UNIQUE constraint on (`profile_id`, `category`, `setting_name`)
*   **`logs` table:**
    *   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    *   `profile_id` (INTEGER NOT NULL, FOREIGN KEY to `profiles.id` ON DELETE CASCADE)
    *   `timestamp` (TEXT NOT NULL, ISO format)
    *   `log_text` (TEXT NOT NULL)

The `database.py` script initializes this database and its tables if they don't exist upon module import or direct execution.

### Public API (`system_sage_core/olb_api.py`):

The following functions are provided for external use by SystemSage:

*   **`get_all_profiles() -> List[Dict[str, Any]]`**
    *   **Purpose:** Retrieves a summary list of all stored overclocking profiles.
    *   **Returns:** A list of dictionaries. Each dictionary represents a profile summary and includes keys: `id`, `name`, `description`, `last_modified_date`. Returns an empty list if no profiles exist or an error occurs.
    *   **Expected Inputs:** None.

*   **`get_profile_details(profile_id: int) -> Optional[Dict[str, Any]]`**
    *   **Purpose:** Retrieves detailed information for a specific profile, including its settings and associated log entries.
    *   **Expected Inputs:**
        *   `profile_id` (int): The unique ID of the profile to retrieve.
    *   **Returns:** A dictionary containing the profile details (e.g., `id`, `name`, `description`, `creation_date`, `last_modified_date`). This dictionary will also have a 'settings' key (a list of setting dictionaries: `id`, `profile_id`, `category`, `setting_name`, `setting_value`, `value_type`) and a 'logs' key (a list of log dictionaries: `id`, `profile_id`, `timestamp`, `log_text`). Returns `None` if the profile is not found or an error occurs.

*   **`create_new_profile(name: str, description: Optional[str] = None, initial_settings: Optional[List[Dict[str, Any]]] = None, initial_logs: Optional[List[str]] = None) -> Optional[int]`**
    *   **Purpose:** Creates a new overclocking profile with optional initial settings and log entries.
    *   **Expected Inputs:**
        *   `name` (str): The name for the new profile.
        *   `description` (str, optional): An optional description for the profile.
        *   `initial_settings` (List[Dict[str, Any]], optional): A list of settings to add. Each setting dictionary should contain:
            *   `category` (str): e.g., "CPU", "Memory".
            *   `setting_name` (str): e.g., "CoreVoltage", "Frequency".
            *   `setting_value` (str): The value of the setting.
            *   `value_type` (str): The type of the value (e.g., "float", "int", "str").
        *   `initial_logs` (List[str], optional): A list of log text strings to add as initial log entries.
    *   **Returns:** The ID (int) of the newly created profile, or `None` if creation fails.

*   **`update_existing_profile(profile_id: int, name: Optional[str] = None, description: Optional[str] = None, settings_to_add: Optional[List[Dict[str, Any]]] = None, settings_to_update: Optional[List[Dict[str, Any]]] = None, setting_ids_to_delete: Optional[List[int]] = None, logs_to_add: Optional[List[str]] = None) -> bool`**
    *   **Purpose:** Updates an existing profile's name, description, settings, and/or logs.
    *   **Expected Inputs:**
        *   `profile_id` (int): The ID of the profile to update.
        *   `name` (str, optional): New name for the profile.
        *   `description` (str, optional): New description for the profile.
        *   `settings_to_add` (List[Dict[str, Any]], optional): List of new settings to add (same structure as in `create_new_profile`).
        *   `settings_to_update` (List[Dict[str, Any]], optional): List of settings to update. Each dictionary should contain:
            *   `id` (int): The ID of the setting to update.
            *   `setting_value` (str): The new value for the setting.
        *   `setting_ids_to_delete` (List[int], optional): List of setting IDs to delete.
        *   `logs_to_add` (List[str], optional): List of new log text strings to add.
    *   **Returns:** `True` if any update operation was attempted (even if some sub-operations fail), `False` if the profile doesn't exist or no update parameters were provided.

*   **`delete_profile_by_id(profile_id: int) -> bool`**
    *   **Purpose:** Deletes a profile and all its associated settings and logs (due to CASCADE DELETE in the database).
    *   **Expected Inputs:**
        *   `profile_id` (int): The ID of the profile to delete.
    *   **Returns:** `True` if the profile was successfully deleted, `False` otherwise.

*   **`add_log_to_profile(profile_id: int, log_text: str) -> Optional[int]`**
    *   **Purpose:** Adds a new log entry to a specific existing profile.
    *   **Expected Inputs:**
        *   `profile_id` (int): The ID of the profile to add the log to.
        *   `log_text` (str): The text content of the log entry.
    *   **Returns:** The ID (int) of the newly created log entry, or `None` if it fails (e.g., profile not found).

### Data Models (`system_sage_core/profiles.py`):

*   **`Profile` Class:** (As previously documented, used implicitly by the API)
    *   Attributes: `id`, `name`, `type`, `settings` (dict), `notes`.
*   **`SettingsCategory` Class:** (As previously documented, currently not directly used by the API but defines a related concept)
    *   Attributes: `id`, `name`, `description`.

## Integration Plan Considerations for SystemSage

*   SystemSage will need to bundle the `system_sage_core` package (from the `feature/system-sage-refactor` branch of the OCL repository) or ensure it's installed in its environment. This includes `olb_api.py`, `database.py`, `profiles.py`, and the `system_sage_olb.db` file (which will be created/managed by `database.py`).
*   The SystemSage GUI will use the functions in `olb_api.py` to manage and display OCL profiles and their details.
*   Error handling (e.g., `None` returns, `False` returns, or empty lists) from the API should be managed by SystemSage to provide appropriate feedback to the user.
```
