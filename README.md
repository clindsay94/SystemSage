# System Sage - V2.2 (Enhanced DevEnvAudit Integration)

**Your intelligent PC software inventory, developer environment, and overclocking logbook analysis tool.**

System Sage is a Python application with a Graphical User Interface (GUI) designed to provide users with a comprehensive understanding and management suite for their Windows system. It integrates three core modules:
1.  **System Inventory:** Queries the Windows Registry for installed software, validates paths, and calculates disk usage.
2.  **Developer Environment Audit (DevEnvAudit):** A powerful module that analyzes development tools, configurations, environment variables, and potential issues in your dev setup. Its results are displayed in detail within a dedicated GUI tab and included in combined system reports.
3.  **Overclocker's Logbook (OCL):** Manages overclocking profiles and logs, leveraging a local SQLite database, with its own dedicated GUI tab.

This project is primarily developed by Connor Lindsay (clindsay94) with Gemini AI assistance.

## Core Features

*   **Graphical User Interface (GUI):** System Sage now runs as a GUI application, providing a user-friendly way to initiate scans and view results in organized tabs for "System Inventory," "Developer Environment Audit," and "Overclocker's Logbook."
*   **Comprehensive Software Inventory:**
    *   Scans multiple registry hives for installed applications and components.
    *   Validates installation paths and calculates disk usage (toggleable).
    *   Categorizes entries and provides actionable remarks (orphans, broken paths, launcher hints).
*   **In-Depth Developer Environment Audit (via integrated DevEnvAudit module):**
    *   Identifies a wide range of installed development tools (IDEs, languages, SDKs, VCS, etc.) and their versions.
    *   Collects and analyzes system and user environment variables, highlighting potential issues (e.g., incorrect PATH entries).
    *   Detects common issues and misconfigurations in development setups.
    *   Results (detected tools, environment variables, issues) are displayed in structured Treeview tables within the "Developer Environment Audit" GUI tab.
    *   Current DevEnvAudit configuration (scan paths, exclusions) can be viewed within its GUI tab.
    *   (Planned: Filtering and sorting options for DevEnvAudit results).
*   **Overclocker's Logbook (OCL) Module Integration:**
    *   Manages overclocking profiles (BIOS/UEFI settings, memory timings, CPU OC, etc.).
    *   View profile lists, details (settings & logs), create new (simplified) profiles, and add log entries.
    *   Data stored in a local SQLite database (`ocl_module_src/system_sage_olb.db`).
    *   Placeholder for future PC-to-Android profile synchronization.
    *   OCL API and architecture documented in `docs/architecture.md`.
*   **Combined Reporting:**
    *   Generate comprehensive JSON and Markdown reports via the GUI ("File" > "Save Combined Report").
    *   Reports include full data from System Inventory and Developer Environment Audit scans.
*   **Externalized Configuration:**
    *   SystemSage keywords/hints: `systemsage_component_keywords.json`, `systemsage_launcher_hints.json`.
    *   DevEnvAudit settings: `devenvaudit_src/devenvaudit_config.json`, `devenvaudit_src/tools_database.json`, `devenvaudit_src/software categorization database.json`.
*   **Error Handling:** Includes error handling for registry access, file operations, and scan processes.

## How to Run System Sage

1.  **Prerequisites:**
    *   Python 3.x installed on your Windows system (Tkinter support is usually included).
    *   The script `SystemSageV1.2.py` (or the latest version).
    *   The `devenvaudit_src/` directory and its contents (all DevEnvAudit module files).
    *   The `ocl_module_src/` directory and its contents.
    *   Relevant JSON configuration files (defaults may apply if some are missing).

2.  **Open a Command Prompt or PowerShell.**
3.  **Navigate to the directory** where SystemSage files are saved.
4.  **Run the script:**
    ```sh
    python SystemSageV1.2.py [options]
    ```
    This launches the System Sage GUI.

## Using the GUI

*   **Main Window:** Tabs for "System Inventory," "Developer Environment Audit," and "Overclocker's Logbook."
*   **Running Scans:**
    *   Use the "Scan" menu to start "System Inventory Scan" or "Run DevEnv Audit."
    *   Scan progress updates in the status bar. Results populate the respective tabs.
    *   For DevEnvAudit, view its current configuration via the "View/Refresh Loaded Configuration" button in its tab.
*   **OCL Profiles:** Managed within the "Overclocker's Logbook" tab (refresh list, view details, save new, add log).
*   **Saving Reports:** "File" > "Save Combined Report (JSON & MD)" saves System Inventory and DevEnvAudit data.

## Command-Line Options

While System Sage is primarily GUI-driven, some CLI options can set initial defaults for GUI operations:
*   `--output-dir <directory_name>`: Default output directory for reports.
*   `--no-disk-usage`: Affects System Inventory's disk usage calculation default.
*   `--md-include-components` / `--md-no-components`: Default for System Inventory components in Markdown.
*   `--run-devenv-audit`: GUI initiated; flag noted but no separate CLI scan.
*   `--help`: Shows CLI help and exits.

*Note: Direct CLI report generation without GUI is not a primary feature of this version.*

## Known Issues & Omissions (This iteration)

*   **DevEnvAudit HTML Report Formatting:** The planned refactor of `devenvaudit_src/report_generator.py` to improve HTML data serialization (especially for complex/nested data) was not successfully implemented due to persistent tool errors during file modification attempts. HTML reports from DevEnvAudit might not render complex data structures optimally.
*   **OCL Data in Combined Reports:** Summaries of OCL profiles are NOT included in the main JSON/Markdown reports due to persistent tool errors preventing the necessary code changes.
*   **Unit Tests for OCL Integration:** Were NOT implemented due to persistent tool errors preventing test file creation/modification.
*   **Unit Tests for DevEnvAudit Integration:** (Planned for this version, status pending).
*   **`README.txt` Outdated:** The old `README.txt` file is outdated. This `README.md` is the current primary documentation.

## Future Planned Features

*   Full implementation of "Save Current System Configuration as New OCL Profile" with actual system data capture.
*   Full implementation of "Update Selected OCL Profile" with detailed editing capabilities.
*   OCL Profile Synchronization (PC-to-Android).
*   Filtering/Sorting for DevEnvAudit results in GUI.
*   Editable DevEnvAudit configuration in GUI.
*   Interactive Orphan/Bad Path Management (System Inventory).
*   Advanced Filtering & Sorting in GUI (System Inventory).
*   Configuration GUI for all settings.
*   Refined CLI Mode.
*   Executable Bundling.

## Development & Acknowledgements

This project is primarily developed by **Connor Lindsay (clindsay94)**.
The `devenvaudit_src` modules are from the DevEnvAudit project.
The `ocl_module_src` modules are from the Overclocker's Logbook project.
Significant AI assistance provided by Gemini (Google).

## License

This project is licensed under the MIT License. See `LICENSE.txt` for details.
```
