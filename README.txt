# System Sage - V2.0 (GUI Edition)

**Your intelligent PC software inventory and developer environment analysis tool.**

System Sage is a Python application designed to help users gain a deeper understanding of the software installed on their Windows system and analyze their development environment. It features a Graphical User Interface (GUI) to manage scans and view results. System Sage queries the Windows Registry for installed software, validates paths, calculates disk usage, and integrates the **DevEnvAudit** tool to provide insights into your development tools, configurations, and potential issues.

This project is primarily developed by Connor Lindsay (clindsay94) with Gemini AI assistance and is currently under active development.

## Core Features

*   **Graphical User Interface (GUI):** System Sage now runs as a GUI application, providing a user-friendly way to initiate scans and view results in organized tabs.
*   **Comprehensive Software Inventory:** Scans multiple registry hives (`HKEY_LOCAL_MACHINE` for 64-bit and 32-bit apps, and `HKEY_CURRENT_USER`) for installed applications and components. (Via System Inventory scan)
*   **Developer Environment Audit:** Integrates functionality from DevEnvAudit to:
    *   Identify installed development tools (IDEs, languages, SDKs, etc.) and their versions.
    *   Collect and analyze system and user environment variables.
    *   Detect common issues and misconfigurations in a development setup.
*   **Path Validation & Disk Usage:** Checks registry `InstallLocation` paths and can calculate disk space for installed software (toggleable for speed).
*   **Categorization & Remarks:** Intelligently categorizes software vs. components and provides actionable remarks (e.g., potential orphans, broken paths, game launcher hints).
*   **Combined Reporting:**
    *   **JSON File (`system_sage_combined_report.json`):** Outputs a detailed, structured report containing both system inventory and DevEnvAudit results. The top level includes `systemInventory` and `devEnvAudit` keys.
    *   **Markdown File (`system_sage_combined_report.md`):** Generates a human-readable report with sections for System Inventory and Developer Environment Audit findings.
    *   Reports are saved via a GUI menu option, allowing the user to choose the output directory.
*   **Externalized Configuration:**
    *   Component detection keywords are configurable via `systemsage_component_keywords.json`.
    *   Game launcher hints are configurable via `systemsage_launcher_hints.json`.
*   **Error Handling:** Includes error handling for registry access, file operations, and scan processes.

## How to Run System Sage

1.  **Prerequisites:**
    *   Python 3.x installed on your Windows system (Tkinter support is usually included).
    *   The script `SystemSageV1.2.py` (or the latest version) and the `devenvaudit_src` subdirectory with its contents.
    *   Configuration files: `systemsage_component_keywords.json` and `systemsage_launcher_hints.json` (defaults are used if missing).

2.  **Open a Command Prompt or PowerShell.**

3.  **Navigate to the directory** where you've saved the SystemSage files.
    ```sh
    cd path\to\your\SystemSage
    ```

4.  **Run the script:**
    ```sh
    python SystemSageV1.2.py [options]
    ```
    This will launch the System Sage GUI.

## Using the GUI

*   **Main Window:** The GUI presents two main tabs: "System Inventory" and "Developer Environment Audit".
*   **Running Scans:**
    *   Use the "Scan" menu to start either the "System Inventory Scan" or the "Run DevEnv Audit".
    *   Scan progress and status will be updated in the status bar at the bottom.
    *   Results will populate the respective tabs.
*   **Saving Reports:**
    *   Go to "File" > "Save Combined Report (JSON & MD)".
    *   You will be prompted to select an output directory. Both JSON and Markdown reports containing data from executed scans will be saved there.

## Command-Line Options

While System Sage V2.0 is primarily a GUI application, some command-line options can influence its initial behavior or default settings used by the GUI:

*   `--output-dir <directory_name>`: Sets the default directory initially proposed when saving reports. (Default: "output")
*   `--no-disk-usage`: If provided, the "Calculate Disk Usage" option (if implemented as a GUI checkbox) might be unchecked by default, or this setting will be used for scans initiated from a context that respects it. System Inventory scans run from the GUI currently use this flag's value.
*   `--md-include-components` / `--md-no-components`: Influences whether SystemSage's own components list is detailed in the Markdown report by default.
*   `--console-include-components` / `--console-no-components`: (Primarily for V1 legacy behavior) These flags' effects on direct console output are reduced as the primary output is now the GUI.
*   `--run-devenv-audit`: (Primarily for V1 legacy behavior) The DevEnvAudit scan is now initiated via the GUI. This flag, if passed, is noted by the GUI but doesn't trigger a separate CLI scan before GUI launch.
*   `--help`: Show a help message listing all available options and exit (this will still work before the GUI launches).

*Note: Direct generation of JSON/Markdown reports from the command line without launching the GUI is not the primary mode of operation for V2.0 but could be added if needed.*

## Future Planned Features

System Sage is an evolving tool. Potential future enhancements include:

*   **Interactive Orphan/Bad Path Management:** (As originally planned) Guided review and actions for problematic registry entries.
*   **Deeper File System Analysis:** For entries with no registry `InstallLocation`.
*   **Advanced Filtering & Sorting in GUI:** More granular control over displayed results.
*   **Configuration GUI:** A dedicated section or dialog within the GUI to manage settings (scan paths for DevEnvAudit, keyword files, etc.).
*   **Refined CLI Mode:** Option for direct CLI execution and report generation without GUI for automation.
*   **Executable Bundling:** Packaging SystemSage as a standalone executable.

## Development & Acknowledgements

This project is primarily developed by **Connor Lindsay (clindsay94)**.

Significant portions of the code structure, logic refinement, and feature implementation have been developed in collaboration with Gemini, a large language model from Google. This collaborative approach has been instrumental in the rapid development and evolution of SystemSage.
The `devenvaudit_src` modules were originally from the DevEnvAudit project, also by clindsay94.

## Contributing & Feedback

Feedback, bug reports, and feature suggestions are welcome!

## License

This project is licensed under the MIT License. See the `LICENSE.txt` file for details.

---

*System Sage - Helping you understand and manage your PC, one registry key and dev tool at a time!*