# System Sage - V2.1 (OCL Integration)

**Your intelligent PC software inventory, developer environment, and overclocking logbook analysis tool.**

System Sage is a Python application with a Graphical User Interface (GUI) designed to provide users with a comprehensive understanding and management suite for their Windows system. It now integrates:
1.  **System Inventory:** Queries the Windows Registry for installed software, validates paths, and calculates disk usage.
2.  **Developer Environment Audit (DevEnvAudit):** Analyzes development tools, configurations, and potential issues.
3.  **Overclocker's Logbook (OCL):** Manages overclocking profiles and logs, leveraging a local SQLite database.

This project is primarily developed by Connor Lindsay (clindsay94) with Gemini AI assistance.

## Core Features

*   **Graphical User Interface (GUI):** System Sage now runs as a GUI application, providing a user-friendly way to initiate scans and view results in organized tabs for System Inventory, Developer Environment Audit, and Overclocker's Logbook.
*   **Comprehensive Software Inventory:** Scans multiple registry hives (`HKEY_LOCAL_MACHINE` for 64-bit and 32-bit apps, and `HKEY_CURRENT_USER`) for installed applications and components. (Via System Inventory scan)
*   **Developer Environment Audit:** Integrates functionality from DevEnvAudit to:
    *   Identify installed development tools (IDEs, languages, SDKs, etc.) and their versions.
    *   Collect and analyze system and user environment variables.
    *   Detect common issues and misconfigurations in a development setup.
*   **Overclocker's Logbook (OCL) Module Integration:**
    *   Manages overclocking profiles (BIOS/UEFI settings, memory timings, CPU OC, etc.).
    *   Allows viewing a list of profiles, their details (settings and logs).
    *   Supports creating new (simplified) profiles and adding log entries to existing ones.
    *   Profile data is stored in a local SQLite database (`ocl_module_src/system_sage_olb.db`).
    *   Includes a placeholder for future PC-to-Android profile synchronization.
    *   The OCL module's API and architecture are documented in `docs/architecture.md`.
*   **Path Validation & Disk Usage:** Checks registry `InstallLocation` paths and can calculate disk space for installed software (toggleable for speed).
*   **Categorization & Remarks:** Intelligently categorizes software vs. components and provides actionable remarks (e.g., potential orphans, broken paths, game launcher hints).
*   **Combined Reporting (Intended, but with issues):**
    *   JSON & Markdown report generation is available via the GUI.
    *   These reports include System Inventory and DevEnvAudit data.
    *   *Known Issue:* Integration of OCL profile summaries into these reports was attempted but not successfully implemented due to subtask execution errors.
*   **Externalized Configuration:**
    *   SystemSage component keywords: `systemsage_component_keywords.json`.
    *   SystemSage launcher hints: `systemsage_launcher_hints.json`.
    *   DevEnvAudit tool definitions: `devenvaudit_src/tools_database.json`.
    *   DevEnvAudit configuration: `devenvaudit_src/devenvaudit_config.json`.
*   **Error Handling:** Includes error handling for registry access, file operations, and scan processes.

## How to Run System Sage

1.  **Prerequisites:**
    *   Python 3.x installed on your Windows system (Tkinter support is usually included).
    *   The script `SystemSageV1.2.py` (or the latest version).
    *   The `devenvaudit_src` directory and its contents.
    *   The `ocl_module_src` directory and its contents (from the `feature/system-sage-refactor` branch of `clindsay94/Overclockers-Logbook`).
    *   Configuration files (defaults are used if missing for some): `systemsage_component_keywords.json`, `systemsage_launcher_hints.json`.

2.  **Open a Command Prompt or PowerShell.**
3.  **Navigate to the directory** where SystemSage files are saved.
4.  **Run the script:**
    ```sh
    python SystemSageV1.2.py [options]
    ```
    This launches the System Sage GUI.

## Using the GUI

*   **Main Window:** Tabs for "System Inventory", "Developer Environment Audit", and "Overclocker's Logbook".
*   **Running Scans:** Use the "Scan" menu for System Inventory and DevEnv Audit. OCL profiles are managed within their tab (e.g., "Refresh Profile List").
*   **Saving Reports:** "File" > "Save Combined Report (JSON & MD)" saves System Inventory and DevEnvAudit data. OCL data is managed separately via its GUI elements.

## Command-Line Options

While System Sage V2.1 is primarily a GUI application, some command-line options can influence its initial behavior or default settings used by the GUI:

*   `--output-dir <directory_name>`: Sets the default directory initially proposed when saving reports. (Default: "output")
*   `--no-disk-usage`: System Inventory scans run from the GUI currently use this flag's value to determine if disk usage should be calculated.
*   `--md-include-components` / `--md-no-components`: Influences whether SystemSage's own components list is detailed in the Markdown report by default.
*   `--run-devenv-audit`: The DevEnvAudit scan is now initiated via the GUI. This flag is noted by the GUI but doesn't trigger a separate CLI scan.
*   `--help`: Shows a help message listing all available options and exit (this will still work before the GUI launches).

*Note: Direct generation of JSON/Markdown reports from the command line without launching the GUI is not the primary mode of operation for V2.1.*

## Known Issues & Omissions (This iteration)

*   **OCL Combined Report Data:** Summaries of OCL profiles are not included in the main JSON/Markdown reports due to subtask execution issues during implementation.
*   **Unit Tests for OCL Integration:** These were planned but not successfully implemented due to subtask execution issues.
*   **README.txt Outdated:** The old `README.txt` file is outdated. This `README.md` is the current documentation.

## Future Planned Features

*   Full implementation of "Save Current System Configuration as New OCL Profile" with actual system data.
*   Full implementation of "Update Selected OCL Profile" with detailed editing capabilities.
*   OCL Profile Synchronization (PC-to-Android).
*   Interactive Orphan/Bad Path Management for System Inventory.
*   Advanced Filtering & Sorting in GUI for all data types.
*   Configuration GUI for managing settings.
*   Refined CLI Mode for automation.
*   Executable Bundling.

## Development & Acknowledgements

This project is primarily developed by **Connor Lindsay (clindsay94)**.
The `devenvaudit_src` modules are from the DevEnvAudit project.
The `ocl_module_src` modules are from the Overclocker's Logbook project.
Significant AI assistance provided by Gemini (Google).

## License

This project is licensed under the MIT License. See `LICENSE.txt` for details.
```
