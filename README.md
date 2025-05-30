# System Sage - V2.0

**Your intelligent PC software inventory, developer environment, and overclocking logbook analysis tool.**

System Sage is a Python application with a Graphical User Interface (GUI) designed to provide users with a comprehensive understanding and management suite for their Windows system. The GUI is built using **CustomTkinter** for a modern look and feel. It integrates three core modules:
1.  **System Inventory:** Queries the Windows Registry for installed software, validates paths, and calculates disk usage.
2.  **Developer Environment Audit (DevEnvAudit):** A powerful module that analyzes development tools, configurations, environment variables, and potential issues in your dev setup. Its results are displayed in detail within a dedicated GUI tab and included in combined system reports.
3.  **Overclocker's Logbook (OCL):** Manages overclocking profiles and logs, leveraging a local SQLite database, with its own dedicated GUI tab.

This project is primarily developed by Connor Lindsay (clindsay94) with Gemini AI assistance.

*Note: The UI has been significantly overhauled using CustomTkinter. Screenshots in this README may be outdated and will be updated in a future revision to reflect the new appearance.*

## Core Features


*   **Graphical User Interface (GUI):** System Sage now runs as a GUI application, built with **CustomTkinter** to provide a modern user experience. It offers a user-friendly way to initiate scans and view results in organized tabs for "System Inventory," "Developer Environment Audit," and "Overclocker's Logbook." Standard dialogs have been replaced with CustomTkinter equivalents for a consistent look and feel.
*   **Comprehensive Software Inventory:**
    *   Scans multiple registry hives for installed applications and components.
    *   Validates installation paths and calculates disk usage (toggleable).
    *   Categorizes entries and provides actionable remarks (orphans, broken paths, launcher hints).
*   **In-Depth Developer Environment Audit (via integrated DevEnvAudit module):**
    *   Identifies a wide range of installed development tools (IDEs, languages, SDKs, VCS, etc.) and their versions.
    *   Collects and analyzes system and user environment variables, highlighting potential issues (e.g., incorrect PATH entries).
    *   Detects common issues and misconfigurations in development setups.
    *   Results (detected tools, environment variables, issues) are displayed in structured tables using **`CTkTable`** (a CustomTkinter-compatible table widget) within the "Developer Environment Audit" GUI tab.

*   **Overclocker's Logbook (OCL) Module Integration:**
    *   Manages overclocking profiles (BIOS/UEFI settings, memory timings, CPU OC, etc.).
    *   View profile lists, details (settings & logs), create new (simplified) profiles, and add log entries.
    *   Data stored in a local SQLite database (`ocl_module_src/system_sage_olb.db`).
*   **Combined Reporting:**
    *   Generate comprehensive JSON and Markdown reports via the GUI ("File" > "Save Combined Report").
    *   Reports include full data from System Inventory and Developer Environment Audit scans.
*   **Externalized Configuration:**
    *   SystemSage keywords/hints: `systemsage_component_keywords.json`, `systemsage_launcher_hints.json`.
    *   DevEnvAudit settings: `devenvaudit_src/devenvaudit_config.json`, `devenvaudit_src/tools_database.json`, `devenvaudit_src/software categorization database.json`.
    *   AI Core (future): Will include configuration for model paths, parameters, etc.
*   **Error Handling:** Includes error handling for registry access, file operations, and scan processes.

## How to Run System Sage

1.  **Prerequisites:**

    *   Python 3.x installed on your Windows system.
    *   `customtkinter` library: `pip install customtkinter`
    *   `CTkTable` library: `pip install CTkTable`

    *   The script `SystemSageV2.0.py` (or the latest version).
    *   The `devenvaudit_src/` directory and its contents.
    *   The `ocl_module_src/` directory and its contents.
    *   Relevant JSON configuration files (defaults may apply if some are missing).

2.  **Open a Command Prompt or PowerShell.**
3.  **Navigate to the directory** where SystemSage files are saved.
4.  **Run the script:**
    ```sh
    python SystemSageV2.0.py [options]
    ```
    This launches the System Sage GUI.

## Using the GUI

*   **Main Window:** Tabs for "System Inventory," "Developer Environment Audit," and "Overclocker's Logbook."
*   **Running Scans:**
    *   Use the "Scan" menu to start "System Inventory Scan" or "Run DevEnv Audit."
    *   Scan progress updates in the status bar. Results populate the respective tabs.
*   **OCL Profiles:** Managed within the "Overclocker's Logbook" tab.
*   **Saving Reports:** "File" > "Save Combined Report (JSON & MD)" saves System Inventory and DevEnvAudit data.

## Command-Line Options

While System Sage is primarily GUI-driven, some CLI options can set initial defaults for GUI operations:
*   `--output-dir <directory_name>`: Default output directory for reports.
*   `--no-disk-usage`: Affects System Inventory's disk usage calculation default.
*   `--md-include-components` / `--md-no-components`: Default for System Inventory components in Markdown.
*   `--help`: Shows CLI help and exits.

*Note: Direct CLI report generation without GUI is not a primary feature of this version.*

## Known Issues & Omissions (V2.0)

*   **DevEnvAudit HTML Report Formatting:** The planned refactor of `devenvaudit_src/report_generator.py` to improve HTML data serialization was not implemented.
*   **OCL Data in Combined Reports:** Summaries of OCL profiles are NOT included in the main JSON/Markdown reports.
*   **Unit Tests:** Comprehensive unit tests for OCL and DevEnvAudit integration are pending.
*   **`README.txt` Outdated:** The old `README.txt` file is outdated. This `README.md` is the current primary documentation.

## Future Planned Features

*   **OCL Enhancements:**
    *   Full implementation of "Save Current System Configuration as New OCL Profile" with actual system data capture.
    *   Full implementation of "Update Selected OCL Profile" with detailed editing capabilities.
    *   OCL Profile Synchronization (PC-to-Android).
*   **GUI Enhancements:**
    *   Filtering/Sorting for DevEnvAudit results in GUI.
    *   Editable DevEnvAudit configuration in GUI.
    *   Interactive Orphan/Bad Path Management (System Inventory).
    *   Advanced Filtering & Sorting in GUI (System Inventory).
    *   Configuration GUI for all settings.
*   **General:**
    *   - Potential Future AI Enhancements: Exploration of AI-driven analytical capabilities to further enhance system insights and user assistance.
    *   Refined CLI Mode with more comprehensive reporting options.
    *   Executable Bundling (e.g., using PyInstaller).
    *   Comprehensive Unit Test Coverage.

## Development & Acknowledgements

This project is primarily developed by **Connor Lindsay (clindsay94)**.
The `devenvaudit_src` modules are from the DevEnvAudit project.
The `ocl_module_src` modules are from the Overclocker's Logbook project.
Significant AI assistance provided by Gemini (Google).

## License

This project is licensed under the MIT License. See `LICENSE.txt` for details.
```
