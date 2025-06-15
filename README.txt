
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
    *   Game launcher hints are configurable via `systemsage_software_hints.json`.
*   **Error Handling:** Includes error handling for registry access, file operations, and scan processes.


## How to Run System Sage

System Sage can be run via its command-line interface or its new graphical user interface.

1.  **Prerequisites:**

    *   Python 3.x installed on your Windows system (Tkinter support is usually included).
    *   The script `SystemSageV1.2.py` (or the latest version) and the `devenvaudit_src` subdirectory with its contents.
    *   Configuration files: `systemsage_component_keywords.json` and `systemsage_software_hints.json` (defaults are used if missing).

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


System Sage is an evolving tool. Here are some features planned for future development, grouped by focus area:

### Core Functionality Enhancements

*   **Deeper File System Analysis:**
    *   For entries with no registry `InstallLocation`, attempt to locate corresponding application folders/executables on specified drives or common installation directories.
    *   Analyze folder contents to better identify application types or associated files.
*   **Startup Program Analysis:**
    *   List programs configured to run at system startup (from Registry, Startup folders).
    *   Provide information about the impact of startup items.
    *   Allow users to manage (enable/disable) startup entries (with appropriate permissions).
*   **Duplicate Finder:**
    *   Identify potentially duplicate installations of the same software based on name, version, or installation path heuristics.
    *   Offer a review process for users to confirm and manage duplicates.
*   **Change History/Snapshots:**
    *   Allow users to save a snapshot of the current software inventory.
    *   Compare different snapshots to identify changes over time (newly installed, uninstalled, or updated software).

### Interactive Features & Management

*   **Interactive Orphan/Bad Path Management:**
    *   Guided review of entries flagged as "Potential Orphan?" or "Broken install path."
    *   Options to attempt automated file system searches for orphaned entries based on application name or publisher.
    *   User-confirmed actions to update incorrect `InstallLocation` values in the registry.
    *   User-confirmed actions to (securely) back up and offer deletion of orphaned registry keys.
*   **Desktop Shortcut Management:**
    *   List all desktop shortcuts (.lnk files).
    *   Analyze shortcuts to identify their targets, working directories, and validity.
    *   Flag broken shortcuts or shortcuts pointing to uninstalled applications.
    *   Offer options to clean up or repair problematic shortcuts.

### Reporting & Output

*   **Advanced Filtering & Sorting:**
    *   More granular control over filtering and sorting the output based on criteria such as:
        *   Installation date (if available).
        *   Disk size.
        *   Publisher.
        *   Category (Application/Component).
        *   Last used date (see "Software Usage Tracking Integration").
*   **System Health/Bloat Score:**
    *   A calculated score or qualitative assessment based on factors like:
        *   Number of orphaned registry entries.
        *   Volume of broken installation paths.
        *   Presence of potentially unwanted programs (PUPs) (requires definition).
        *   Large applications that haven't been used in a long time (requires usage tracking).
    *   Provide recommendations based on the score.

### User Experience & Interface

*   **Enhanced User Interface:**
    *   Potential for a more interactive command-line interface (e.g., using `prompt_toolkit` for guided actions).
    *   Future consideration for a basic Graphical User Interface (GUI) for easier navigation and management.
*   **Localization:**
    *   Support for multiple languages in the UI and reports.

### Extensibility & Customization

*   **External Configuration:**
    *   Allow customization of keywords (for components, launchers, potentially PUPs) via external configuration files (e.g., JSON, YAML).
    *   User-defined rules for categorization or remark generation.
*   **Plugin System:**
    *   Develop a plugin architecture to allow community contributions for:
        *   Specific application detection modules.
        *   Custom analysis routines (e.g., for niche software types).
        *   New report formats.
*   **Portable Mode:**
    *   Offer a version of System Sage that can run without installation (e.g., from a USB drive), keeping configuration and output self-contained.

### Ambitious Long-Term Goals

*   **Software Usage Tracking Integration (Ambitious & Complex):**
    *   Investigate methods to estimate last used dates for applications. This might involve:
        *   Checking system event logs (limited).
        *   Analyzing prefetch files or other OS artifacts (requires deep OS knowledge).
        *   Integrating with known application-specific logs if APIs or standards exist (unlikely to be universal).
    *   *This is a highly complex feature and may require external tools, advanced permissions, or have significant limitations.*

## Development & Acknowledgements

This project is primarily developed by **Connor Lindsay (clindsay94)**.

Significant portions of the code structure, logic refinement, and feature implementation have been developed in collaboration with Gemini, a large language model from Google. This collaborative approach has been instrumental in the rapid development and evolution of SystemSage.
The `devenvaudit_src` modules were originally from the DevEnvAudit project, also by clindsay94.

## Contributing & Feedback

Feedback, bug reports, and feature suggestions are welcome!

## License

This project is licensed under the MIT License. See the `LICENSE.txt` file for details.

---

System Sage: Gaze Deeper into Your PC, for the Wise to see. (insert poorly drawn sage here)

