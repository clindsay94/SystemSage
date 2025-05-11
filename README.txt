# System Sage - V1.2

**Your intelligent PC software inventory and analysis tool.**

System Sage is a Python script designed to help users gain a deeper understanding of the software installed on their Windows system. It queries the Windows Registry to gather detailed information, validates installation paths, calculates disk usage, and provides contextual remarks to help identify and manage your software landscape. This tool is particularly useful for tech enthusiasts, power users, and anyone looking to maintain a clean and efficient PC environment.

This project is primarily developed by Connor Lindsay (clindsay94) with Gemini AI assistance and is currently under active development.

## Current Features (V1.2)

* **Comprehensive Software Inventory:** Scans multiple registry hives (`HKEY_LOCAL_MACHINE` for 64-bit and 32-bit apps, and `HKEY_CURRENT_USER`) to find a wide range of installed applications and components.
* **Path Validation:** Checks if the `InstallLocation` specified in the registry exists on the file system.
* **Disk Usage Calculation:** For valid installation paths, System Sage calculates the disk space occupied by the application's directory. This feature can be toggled for faster scans.
* **Categorization:** Intelligently categorizes entries as "Application" or "Component/Driver" based on keywords, helping to distinguish primary software from supporting files.
* **Actionable Remarks:** Provides contextual remarks, including:
    * Identification of games managed by common launchers (Steam, Epic Games, GOG, Battle.net, EA App, Ubisoft Connect, Xbox).
    * Flags for potentially orphaned registry entries (e.g., "Registry entry only (Potential Orphan?)").
    * Indicators for broken installation paths (e.g., "Broken install path (Actionable)").
    * Notes if an `InstallLocation` points to a single file instead of a directory.
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

1.  **Prerequisites:**
    * Python 3.x installed on your Windows system.
    * The script `system_sage_v1.2.py` (or your chosen filename for the latest version).

2.  **Open a Command Prompt or PowerShell.**

3.  **Navigate to the directory** where you've saved the script:
    ```sh
    cd path\to\your\SystemSage
    ```

4.  **Run the script:**
    ```sh
    python system_sage_v1.2.py [options]
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

* Run with default settings:
    ```sh
    python system_sage_v1.2.py
    ```
* Run a quick scan without disk usage and only output to console (showing all entries):
    ```sh
    python system_sage_v1.2.py --no-disk-usage --no-json --no-markdown --console-include-components
    ```
* Save reports to a custom directory:
    ```sh
    python system_sage_v1.2.py --output-dir "C:\SystemSageReports"
    ```

## Future Planned Features

System Sage is an evolving tool. Here are some features planned for future development:

* **Interactive Orphan/Bad Path Management:**
    * Guided review of entries flagged as "Potential Orphan?" or "Broken install path."
    * Options to attempt file system location for orphaned entries.
    * User-confirmed actions to update incorrect `InstallLocation` values in the registry.
    * User-confirmed actions to (securely) back up and delete orphaned registry keys.
* **Deeper File System Analysis:** For entries with no registry `InstallLocation`, attempt to locate corresponding application folders/executables on specified drives.
* **Desktop Shortcut Management:** List, analyze, and potentially manage desktop shortcuts.
* **Advanced Filtering & Sorting:** More granular control over filtering and sorting the output based on various criteria.
* **User Interface:** Potential for a more interactive command-line interface (e.g., using `prompt_toolkit`) or even a basic GUI.
* **External Configuration:** Allow customization of keywords (for components, launchers) via external configuration files.

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

  @media print {
    .ms-editor-squiggler {
        display:none !important;
    }
  }
  .ms-editor-squiggler {
    all: initial;
    display: block !important;
    height: 0px !important;
    width: 0px !important;
  }