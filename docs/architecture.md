# System Sage V2.0 - Application Architecture

This document outlines the architecture of the System Sage V2.0 application, including its core modules: Overclocker's Logbook (OCL) and DevEnvAudit.

<!-- Note to maintainer: An overall architecture diagram illustrating the interaction between SystemSageV2.0.py, the OCL module, and the DevEnvAudit module should be added here. -->

## Main Application (`SystemSageV2.0.py`)

The `SystemSageV2.0.py` script serves as the main entry point and GUI for the application. Its key responsibilities include:

* Providing the main Tkinter-based GUI, including tabs for System Inventory, DevEnvAudit, and Overclocker's Logbook.
* Handling user interactions for initiating scans (System Inventory, DevEnvAudit).
* Displaying results from scans in their respective GUI tabs.
* Interfacing with the OCL module via `ocl_module_src.olb_api` for all OCL-related operations.
* Interfacing with the DevEnvAudit module via `devenvaudit_src.scan_logic` for environment scanning.
* Generating combined JSON and Markdown reports.
* Loading application-level configurations (e.g., `systemsage_component_keywords.json`).

## Overclocker's Logbook (OCL) Module (`ocl_module_src`)

This document outlines the identified Python structure and API of the Overclocker's Logbook (OCL) module, intended for integration with the SystemSage PC application (Version 2.0).

<!-- Note to maintainer: The architecture diagram mentioned at the top of this document should also detail the OCL module's internal structure (database, API layer) and its connection to SystemSageV2.0.py. The following OCL-specific diagram placeholder can be removed or merged. -->
<!-- A diagram illustrating this interaction will be added here. -->

## Repository Structure Overview (OCL)

The OCL module is located at `https://github.com/clindsay94/Overclockers-Logbook` (branch `feature/system-sage-refactor`). While the repository also contains code for a web frontend (TypeScript/HTML), the Python components relevant to SystemSage PC integration are primarily within the `system_sage_core/` subdirectory (which is integrated into SystemSage as `ocl_module_src`).

## Python Module: `ocl_module_src` (Formerly `system_sage_core` in OCL Repo)

This directory is structured as a Python package. It contains the data models, database interaction logic, and the public API for managing overclocking profiles. The data is stored in an SQLite database (`system_sage_olb.db`) within this directory (managed via `resource_path` in `SystemSageV2.0.py` for its expected location).

### Key Python Files (OCL)

* **`ocl_module_src/olb_api.py`**: Defines the public functions SystemSage uses to interact with the OCL module.
* **`ocl_module_src/database.py`**: Handles all SQLite database operations (schema definition, CRUD functions for profiles, settings, and logs). It creates and uses `system_sage_olb.db`.
* **`ocl_module_src/profiles.py`**: Defines the `Profile` and `SettingsCategory` data model classes (though `SettingsCategory` is not directly used by the current API functions, settings are stored with a `category` string).

### Database Schema (`system_sage_olb.db` via `database.py`)

* **`profiles` table:**
  * `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
  * `name` (TEXT NOT NULL)
  * `description` (TEXT)
  * `creation_date` (TEXT NOT NULL, ISO format)
  * `last_modified_date` (TEXT NOT NULL, ISO format)
* **`settings` table:**
  * `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
  * `profile_id` (INTEGER NOT NULL, FOREIGN KEY to `profiles.id` ON DELETE CASCADE)
  * `category` (TEXT NOT NULL)
  * `setting_name` (TEXT NOT NULL)
  * `setting_value` (TEXT)
  * `value_type` (TEXT) - e.g., "str", "int", "float", "bool"
  * UNIQUE constraint on (`profile_id`, `category`, `setting_name`)
* **`logs` table:**
  * `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
  * `profile_id` (INTEGER NOT NULL, FOREIGN KEY to `profiles.id` ON DELETE CASCADE)
  * `timestamp` (TEXT NOT NULL, ISO format)
  * `log_text` (TEXT NOT NULL)

The `database.py` script initializes this database and its tables if they don't exist upon module import or direct execution.

### Public API (`ocl_module_src/olb_api.py`)

The following functions are provided for external use by SystemSage:

* **`get_all_profiles() -> List[Dict[str, Any]]`**
  * **Purpose:** Retrieves a summary list of all stored overclocking profiles.
* **`get_profile_details(profile_id: int) -> Optional[Dict[str, Any]]`**
  * **Purpose:** Retrieves detailed information for a specific profile.
* **`create_new_profile(name: str, description: Optional[str] = None, initial_settings: Optional[List[Dict[str, Any]]] = None, initial_logs: Optional[List[str]] = None) -> Optional[int]`**
  * **Purpose:** Creates a new overclocking profile.
* **`update_existing_profile(...) -> bool`** (arguments omitted for brevity)
  * **Purpose:** Updates an existing profile's name, description, settings, and/or logs.
* **`delete_profile_by_id(profile_id: int) -> bool`**
  * **Purpose:** Deletes a profile and all its associated settings and logs.
* **`add_log_to_profile(profile_id: int, log_text: str) -> Optional[int]`**
  * **Purpose:** Adds a new log entry to a specific existing profile.

## DevEnvAudit Module (`devenvaudit_src`)

(Details of the DevEnvAudit module architecture would go here if this document were to fully centralize all module descriptions. For now, refer to DevEnvAudit's own documentation. SystemSage integrates it as a package.)

* **Interaction with `SystemSageV2.0.py`**: The main application calls `EnvironmentScanner` from `devenvaudit_src.scan_logic` to perform scans and retrieves structured data (components, environment variables, issues) for display and reporting.

## Integration Plan Considerations for SystemSage (Legacy OCL Notes)

* SystemSage bundles `ocl_module_src` (derived from OCL's `system_sage_core`).
* The SystemSage GUI uses functions in `ocl_module_src/olb_api.py`.
* Error handling from the OCL API is managed by SystemSage.
