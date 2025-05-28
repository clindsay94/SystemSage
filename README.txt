# System Sage V1.3

**Your intelligent PC software inventory, development environment analysis, and system management tool.**

System Sage is a comprehensive Python application designed to help users gain a deeper understanding of their Windows system. It combines detailed software inventory from the Windows Registry with a robust audit of the development environment. With an intuitive graphical user interface, System Sage provides valuable insights for system administrators, developers, and enthusiasts alike who need to understand, troubleshoot, or manage their system configurations.

This project is primarily developed by Connor Lindsay (clindsay94) with Gemini AI assistance and is currently under active development.

## Current Features

System Sage has evolved significantly to include advanced system analysis and a user-friendly interface:

* **Comprehensive Software Inventory:** Scans multiple registry hives (`HKEY_LOCAL_MACHINE` for 64-bit and 32-bit apps, and `HKEY_CURRENT_USER`) to find a wide range of installed applications and components.
* **Path Validation:** Checks if the `InstallLocation` specified in the registry exists on the file system.
* **Disk Usage Calculation:** For valid installation paths, System Sage calculates the disk space occupied by the application's directory. This feature can be toggled for faster scans.
* **Categorization:** Intelligently categorizes entries as "Application" or "Component/Driver" based on keywords, helping to distinguish primary software from supporting files.
* **Actionable Remarks:** Provides contextual remarks, including:
    * Identification of games managed by common launchers (Steam, Epic Games, GOG, Battle.net, EA App, Ubisoft Connect, Xbox).
    * Flags for potentially orphaned registry entries (e.g., "Registry entry only (Potential Orphan?)").
    * Indicators for broken installation paths (e.g., "Broken install path (Actionable)").
    * Notes if an `InstallLocation` points to a single file instead of a directory.
* **Developer Environment Audit (DevEnvAudit) Integration:**
    * **Programming Tool Detection:** Identifies installed programming languages, IDEs, version control systems, containers, databases, build tools, and cloud CLIs.
    * **Environment Variable Analysis:** Collects and analyzes system and user environment variables, highlighting discrepancies or missing components.
    * **Issue Identification:** Flags potential issues within the development environment setup.
* **Graphical User Interface (GUI):**
    * **Intuitive Tkinter Interface:** A user-friendly graphical interface for easy navigation and interaction.
    * **Tabbed Views:** Separate tabs for "System Inventory" and "Developer Environment Audit" for organized data presentation.
    * **Responsive Scans:** Both system inventory and DevEnvAudit scans run in threads, ensuring the GUI remains responsive during operations.
    * **Real-time Status Updates:** Provides progress updates in the status bar during scans.
    * **Interactive Data Display:** Results from both scans are displayed in `ttk.Treeview` widgets for easy viewing and filtering.
* **Configurable Scans:** Externalized configuration files for component keywords and launcher hints (`systemsage_component_keywords.json` and `systemsage_launcher_hints.json`) allow for easy customization of scan parameters without modifying core code.
* **Combined Report Generation:** Generates comprehensive JSON and Markdown reports that include data from both System Inventory and DevEnvAudit scans.
* **Flexible Output:**
    * **Console:** Displays a summary of applications (components can be included via command-line flag).
    * **JSON File (`system_sage_inventory.json`):** Outputs a detailed, structured list of all found software entries, perfect for further analysis or use by other tools. Saved to an `output` subdirectory.
    * **Markdown File (`system_sage_inventory.md`):** Generates a human-readable report, with applications and components optionally separated. Includes a section on planned future features. Saved to an `output` subdirectory.
* **Command-Line Interface:** Uses `argparse` to provide control over:
    * Toggling disk usage calculation.
    * Enabling/disabling JSON and Markdown outputs.
    * Specifying the output directory for report files.
    * Controlling whether components/drivers are included in Markdown and console outputs.
* **Error Handling:** Includes error handling for registry access, file operations, and disk size calculations to ensure robustness.

## How to Run System Sage

System Sage can be run via its command-line interface or its new graphical user interface.

1.  **Prerequisites:**
    * Python 3.x installed on your Windows system.
    * The script `system_sage.py` (or your chosen filename for the latest version) and associated files (`devenvaudit.py`, `gui_manager.py`, configuration files, etc.).

2.  **Open a Command Prompt or PowerShell.**

3.  **Navigate to the directory** where you've saved the script:
    ```sh
    cd path\to\your\SystemSage
    ```

4.  **Run the script:**
    * **To launch the GUI (Recommended):**
        ```sh
        python gui_manager.py
        ```
    * **To run the command-line interface:**
        ```sh
        python system_sage.py [options]
        ```

### Command-Line Options:

* `--no-disk-usage`: Disable disk usage calculation for a faster scan. (Default: Enabled)
* `--no-json`: Disable JSON file output. (Default: Enabled)
* `--no-markdown`: Disable Markdown file output. (Default: Enabled)
* `--output-dir <directory_name>`: Specify the directory for output files (e.g., `--output-dir "My Reports"`). (Default: "output")
* `--md-include-components`: Explicitly include components/drivers in the Markdown report.
* `--md-no-components`: Explicitly exclude components/drivers from the Markdown report (overrides default).
    *(If neither `--md-include-components` nor `--md-no-components` is used, the script defaults to including components in Markdown as per `DEFAULT_MARKDOWN_INCLUDE_COMPONENTS = True`)*
* `--console-include-components`: Explicitly include components/drivers in the console output.
* `--console-no-components`: Explicitly exclude components/drivers from the console output (overrides default).
    *(If neither `--console-include-components` nor `--console-no-components` is used, the script defaults to excluding components from console output as per `DEFAULT_CONSOLE_INCLUDE_COMPONENTS = False`)*
* `--help`: Show a help message listing all available options and exit.

**Example Usage:**

* Run with default settings (launches GUI):
    ```sh
    python gui_manager.py
    ```
* Run a quick CLI scan without disk usage and only output to console (showing all entries):
    ```sh
    python system_sage.py --no-disk-usage --no-json --no-markdown --console-include-components
    ```
* Save CLI reports to a custom directory:
    ```sh
    python system_sage.py --output-dir "C:\SystemSageReports"
    ```

## Future Planned Features

System Sage is an evolving tool with a robust roadmap. Here are some features planned for future development:

* **Overclockers-Logbook (OCL) Integration:** Integrate the functionalities of the Overclockers-Logbook, allowing users to log and manage system configuration profiles, expanding beyond just BIOS settings to include memory timings, EXPO, voltage, and other performance-related configurations.
* **Android App Conversion:** Full conversion to a natively deployable Android application using Kivy or a similar framework for on-the-go system auditing.
* **Gemma Integration:** Implement a small, locally run version of Gemma (or a similar lightweight AI model) to analyze collected data from System Sage and DevEnvAudit. This will enable:
    * **Intelligent Diagnostics:** Provide smarter suggestions for system optimization or troubleshooting.
    * **Predictive Analysis:** Identify potential issues before they become critical based on historical data.
    * **Automated Remediation Suggestions:** Offer automated commands or steps to resolve identified problems.
* **Interactive Orphan/Bad Path Management:**
    * Guided review of entries flagged as "Potential Orphan?" or "Broken install path."
    * Options to attempt file system location for orphaned entries.
    * User-confirmed actions to update incorrect `InstallLocation` values in the registry.
    * User-confirmed actions to (securely) back up and delete orphaned registry keys.
* **Deeper File System Analysis:** For entries with no registry `InstallLocation`, attempt to locate corresponding application folders/executables on specified drives.
* **Desktop Shortcut Management:** List, analyze, and potentially manage desktop shortcuts.
* **Advanced Filtering & Sorting:** More granular control over filtering and sorting the output based on various criteria within the GUI and CLI.
* **OS Registry Tweaks Integration:** Tools for logging and applying common operating system registry tweaks and optimizations.
* **Advanced Data Visualization:** More sophisticated graphical representations of system data and trends.
* **Customizable Reporting:** Enhanced options for customizing report content and formats.
* **Performance Benchmarking Integration:** Integrate with system benchmarking tools to log and track performance metrics alongside configuration changes.
* **Cross-Platform Compatibility:** Continued focus on ensuring robust functionality across Windows, macOS, and Linux.

## Development & Acknowledgements

This project is primarily developed by **Connor Lindsay (clindsay94)**.

Significant portions of the code structure, logic refinement, and feature implementation have been developed in collaboration with Gemini, a large language model from Google. This collaborative approach has been instrumental in the rapid development and evolution of System Sage.

## Contributing & Feedback

While this is primarily a personal project, feedback, bug reports, and feature suggestions are welcome! As System Sage continues to develop, your input can be invaluable in shaping it into an even more powerful tool.

*(Consider adding a link to your GitHub issues page here if you plan to use it for tracking.)*

## License

This project is licensed under the MIT License. This means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, provided that the original copyright notice and this permission notice are included in all copies or substantial portions of the Software.

See the `LICENSE` file in the repository for the full license text.

---

*System Sage - Helping you understand and manage your PC, one registry key at a time!*
