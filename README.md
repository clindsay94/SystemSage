# System Sage

**Your intelligent PC software inventory, developer environment auditor, and overclocking logbook.**

System Sage is a modern, GUI-driven Python application designed to give you a comprehensive understanding and management suite for your Windows system. Built with **CustomTkinter** and featuring responsive `ttk.Treeview` tables, it provides a seamless and powerful user experience.

The application integrates three core modules:

1.  **System Inventory:** Scans your system for installed software, drivers, and components.
2.  **Developer Environment Audit (DevEnvAudit):** Analyzes your development tools, environment variables, and system configuration to identify potential issues.
3.  **Overclocker's Logbook (OCL):** A dedicated space to manage and track your hardware overclocking profiles, currently tailored for AMD BIOS settings.

This project is primarily developed by Connor Lindsay (clindsay94) with Gemini AI assistance.

## Core Features

### Modern & Responsive GUI

*   **Unified Interface:** A clean, tab-based interface for "System Inventory," "Developer Environment Audit," and "Overclocker's Logbook."
*   **Interactive Data Tables:** All data is presented in modern `ttk.Treeview` tables, offering full column resizing, sorting, and live filtering capabilities for an efficient workflow.
*   **Consistent Look and Feel:** The entire UI, including dialogs, is built with CustomTkinter for a cohesive and modern aesthetic.

### System Inventory

*   **Deep Scan:** Queries multiple Windows Registry hives to discover installed applications, drivers, and system components.
*   **Detailed Analysis:** Validates installation paths, calculates disk usage (toggleable), and provides actionable remarks (e.g., identifying orphaned entries or broken paths).
*   **Exportable Reports:** Save the complete inventory scan as a `JSON` or `Markdown` file for documentation or further analysis.

### Developer Environment Audit

*   **Comprehensive Tooling Discovery:** Identifies a wide range of installed development tools, including IDEs, languages, SDKs, and version control systems.
*   **Environment Analysis:** Lists all system and user environment variables, with a specific focus on the `PATH` to help diagnose command-line issues.
*   **Problem Detection (Work in Progress):** A growing feature to automatically flag common issues and misconfigurations in your development setup.
*   **Integrated Reporting:** DevEnvAudit results are included in the combined `JSON` and `Markdown` reports.

### Overclocker's Logbook (OCL)

*   **Profile Management:** A dedicated database and interface for saving and managing different hardware tuning profiles. Keep track of changes to BIOS settings, RAM timings, and more.
*   **AMD Focused (Currently):** The initial implementation is tailored for AMD BIOS settings, providing a structured way to log RAM timings and other critical values.
*   **Track Your Tweaks:** Easily compare different profiles to understand the impact of your adjustments, perfect for enthusiasts who fine-tune their systems.

## How to Run System Sage

1.  **Prerequisites:**
    *   Python 3.x installed on your Windows system.
    *   A virtual environment is highly recommended.

2.  **Setup:**
    *   Clone or download the repository.
    *   Open a terminal in the project directory.
    *   Create and activate a virtual environment:

        ```powershell
        # For PowerShell
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        ```

    *   Install the required packages:
        ```sh
        pip install -r requirements.txt
        ```

3.  **Launch the Application:**
    ```sh
    python systemsage_main.py
    ```

## Using the GUI

*   **Run Scans:** Use the "Scan" menu to initiate a "System Inventory Scan" or "Run DevEnv Audit." Progress is shown in the status bar, and results populate the tables in the corresponding tabs.
*   **Manage OCL Profiles:** Use the "Overclocker's Logbook" tab to view, create, and manage your BIOS profiles.
*   **Save Reports:** Go to "File" > "Save Combined Report" to export the data from the System Inventory and DevEnvAudit scans into both `JSON` and `Markdown` formats.

## Future Vision

System Sage was made originally to help me with my own PC environment and software, so it is, for now, tailored more specifically to my own setup. It is under active development, however, with plans to expand its capabilities:

*   **OCL Enhancements:**
    *   **Intel Profile Support:** Broaden the OCL module to include specific settings for Intel platforms. 
    *   **AI-Powered Suggestions:** Explore integrating AI to analyze your profiles and suggest optimized RAM timings or other helpful performance tweaks.
*   **DevEnvAudit Improvements:**
    *   Enhance the problem-detection logic to provide more insightful and actionable recommendations for developers.
*   **General UI/UX:**
    *   Continuously refine the interface, adding more advanced filtering, data visualization, and configuration options directly within the GUI.

## Development & Acknowledgements

*   **Primary Developer:** Connor Lindsay (clindsay94)
*   **AI Assistance:** Gemini (Google) and Jules (Google)
*   **Core Modules:** The `devenvaudit_src` and `ocl_module_src` are adapted from the DevEnvAudit and Overclocker's Logbook projects, respectively.

## License

This project is licensed under the MIT License. See `LICENSE.txt` for details.
