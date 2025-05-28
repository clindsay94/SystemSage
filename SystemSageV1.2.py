# Python Software Inventory & Path Validator v1.2
# This script queries the Windows Registry to list installed software,
# validates installation paths, calculates disk usage for valid paths,
# and outputs to console, JSON, and Markdown.
# V1.2:
# - Output files (JSON, Markdown) are now saved into an "output" subdirectory.
# - Fixed SyntaxWarning for invalid escape sequence in Markdown output.
# - Introduced argparse for command-line arguments.
# - Enhanced "Remarks" for more actionable insights.
# - Added "Future Interactive Features" section to Markdown.
# - User update: Added "Xbox Game" to LAUNCHER_HINTS.

import winreg
import os
import json
import datetime
import argparse
import logging # Added for DevEnvAudit integration
import tkinter as tk
from tkinter import ttk, messagebox, filedialog # Added filedialog
from tkinter import simpledialog # For simple input for OCL
from threading import Thread
import traceback # For logging exceptions from threads

# --- DevEnvAudit Imports ---
from devenvaudit_src.scan_logic import EnvironmentScanner
# --- OCL Module Imports ---
from ocl_module_src import olb_api as ocl_api
from devenvaudit_src.config_manager import load_config as load_devenv_config

# --- Configuration Loading Function ---
def load_json_config(filename, default_data):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Successfully loaded configuration from {filename}")
                return data
        else:
            print(f"Warning: Configuration file {filename} not found. Using default values.")
            # Optionally, create the file with default data here if desired:
            # with open(filename, 'w', encoding='utf-8') as f_out:
            #     json.dump(default_data, f_out, indent=2)
            # print(f"Created {filename} with default values.")
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from {filename}. Using default values.")
    except Exception as e:
        print(f"Warning: Unexpected error loading {filename}: {e}. Using default values.")
    return default_data

# --- Configuration (Defaults, will be overridden by argparse) ---
DEFAULT_CALCULATE_DISK_USAGE = True
DEFAULT_OUTPUT_JSON = True
DEFAULT_OUTPUT_MARKDOWN = True
DEFAULT_MARKDOWN_INCLUDE_COMPONENTS = True
DEFAULT_CONSOLE_INCLUDE_COMPONENTS = False
DEFAULT_OUTPUT_DIR = "output" # V1.2: Default output directory name

DEFAULT_COMPONENT_KEYWORDS = [
    "driver", "sdk", "runtime", "redistributable", "pack", "update for",
    "component", "service", "host", "framework", "module", "tool",
    "package", "library", "interface", "provider", "kit", "utility",
    "microsoft .net", "visual c++", "windows sdk", "directx", "vulkan",
    "intel(r) graphics", "nvidia graphics", "amd chipset", "realtek",
    "msi development", "kits configuration", "windows app certification",
    "winrt intellisense", "universal crt", "windows team extension",
    "windows iot extension", "windows mobile extension", "windows desktop extension",
    "vs_minshell", "vs_community", "vs_filehandler", "vcpp_crt", "dotnet",
    "windows software development kit", "templates", "targeting", "shared framework",
    "apphost", "host fx resolver", "manifest", "toolchain", "addon", "eula"
]

DEFAULT_LAUNCHER_HINTS = {
    "Steam Game": {"publishers": ["valve"], "paths": ["steamapps"]},
    "Epic Games Store Game": {"publishers": ["epic games, inc."], "paths": ["epic games"]},
    "GOG Galaxy Game": {"publishers": ["gog.com"], "paths": ["gog galaxy"]},
    "Battle.net Game": {"publishers": ["blizzard entertainment"], "paths": ["battle.net"]},
    "EA App Game": {"publishers": ["electronic arts"], "paths": ["ea app", "origin games"]},
    "Ubisoft Connect Game": {"publishers": ["ubisoft"], "paths": ["ubisoft game launcher"]},
    "Xbox Game": {"publishers": ["microsoft"], "paths": ["windowsapps", "xboxgames"]},
    "Microsoft Store App": {"publishers": [], "paths": ["windowsapps"]},
}

# Load configurations from JSON files, falling back to defaults
COMPONENT_KEYWORDS_FILE = "systemsage_component_keywords.json"
LAUNCHER_HINTS_FILE = "systemsage_launcher_hints.json"

COMPONENT_KEYWORDS = load_json_config(COMPONENT_KEYWORDS_FILE, DEFAULT_COMPONENT_KEYWORDS)
LAUNCHER_HINTS = load_json_config(LAUNCHER_HINTS_FILE, DEFAULT_LAUNCHER_HINTS)

class DirectorySizeError(Exception):
    """Custom exception for errors during directory size calculation."""
    pass

def is_likely_component(display_name, publisher):
    name_lower = str(display_name).lower()
    publisher_lower = str(publisher).lower()
    for keyword in COMPONENT_KEYWORDS:
        if keyword in name_lower or keyword in publisher_lower:
            return True
    if name_lower.startswith('{') or name_lower.startswith('kb'):
        return True
    return False

def get_hkey_name(hkey_root):
    if hkey_root == winreg.HKEY_LOCAL_MACHINE:
        return "HKEY_LOCAL_MACHINE"
    if hkey_root == winreg.HKEY_CURRENT_USER:
        return "HKEY_CURRENT_USER"
    return str(hkey_root)

def get_directory_size(directory_path, calculate_disk_usage_flag):
    total_size = 0
    if not calculate_disk_usage_flag:
        return 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp) and os.path.exists(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
    except OSError as e:
        raise DirectorySizeError(f"Error accessing directory {directory_path}: {e}") from e
    return total_size

def format_size(size_bytes, calculate_disk_usage_flag):
    if not calculate_disk_usage_flag and size_bytes == 0:
        return "Not Calculated"
    if size_bytes < 0:
        return "N/A (Error)"
    if size_bytes == 0:
        return "0 B" if calculate_disk_usage_flag else "Not Calculated"

    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name)-1 :
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"


def get_installed_software(calculate_disk_usage_flag):
    software_list = []
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (64-bit)"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (32-bit)"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU")
    ]
    processed_entries = set()

    for hkey_root, path_suffix, hive_display_name in registry_paths:
        try:
            with winreg.OpenKey(hkey_root, path_suffix) as uninstall_key:
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                    subkey_name = ""
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        full_reg_key_path = f"{get_hkey_name(hkey_root)}\\{path_suffix}\\{subkey_name}"

                        with winreg.OpenKey(uninstall_key, subkey_name) as app_key:
                            app_details = {
                                'SourceHive': hive_display_name,
                                'RegistryKeyPath': full_reg_key_path,
                                'InstallLocationSize': "N/A" if calculate_disk_usage_flag else "Not Calculated",
                                'Remarks': ""
                            }

                            try:
                                app_details['DisplayName'] = str(winreg.QueryValueEx(app_key, "DisplayName")[0])
                            except FileNotFoundError:
                                app_details['DisplayName'] = subkey_name
                            except OSError as e:
                                app_details['DisplayName'] = f"{subkey_name} (Name Error: {e.strerror})"

                            entry_id_name = app_details['DisplayName']
                            entry_id_version = "N/A"

                            try:
                                app_details['DisplayVersion'] = str(winreg.QueryValueEx(app_key, "DisplayVersion")[0])
                                entry_id_version = app_details['DisplayVersion']
                            except FileNotFoundError:
                                app_details['DisplayVersion'] = "N/A"
                            except OSError as e:
                                app_details['DisplayVersion'] = f"Version Error: {e.strerror}"

                            entry_id = (entry_id_name, entry_id_version)
                            if entry_id in processed_entries:
                                continue
                            processed_entries.add(entry_id)

                            try:
                                app_details['Publisher'] = str(winreg.QueryValueEx(app_key, "Publisher")[0])
                            except FileNotFoundError:
                                app_details['Publisher'] = "N/A"
                            except OSError as e:
                                app_details['Publisher'] = f"Publisher Error: {e.strerror}"

                            app_details['Category'] = "Component/Driver" if is_likely_component(app_details['DisplayName'], app_details['Publisher']) else "Application"

                            try:
                                install_location_raw = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                                install_location_cleaned = str(install_location_raw)

                                if isinstance(install_location_raw, str):
                                    temp_location = install_location_raw.strip()
                                    if (temp_location.startswith('"') and temp_location.endswith('"')) or \
                                       (temp_location.startswith("'") and temp_location.endswith("'")):
                                        install_location_cleaned = temp_location[1:-1]

                                app_details['InstallLocation'] = install_location_cleaned

                                if install_location_cleaned and os.path.isdir(install_location_cleaned):
                                    app_details['PathStatus'] = "OK"
                                    if calculate_disk_usage_flag:
                                        try:
                                            dir_size = get_directory_size(install_location_cleaned, calculate_disk_usage_flag)
                                            app_details['InstallLocationSize'] = format_size(dir_size, calculate_disk_usage_flag)
                                        except DirectorySizeError as e_size:
                                            app_details['InstallLocationSize'] = "N/A (Size Error)"
                                            app_details['Remarks'] += f"Size calc error: {e_size};"

                                elif install_location_cleaned and os.path.isfile(install_location_cleaned):
                                    app_details['PathStatus'] = "OK (File)"
                                    if calculate_disk_usage_flag:
                                        try:
                                            file_size = os.path.getsize(install_location_cleaned)
                                            app_details['InstallLocationSize'] = format_size(file_size, calculate_disk_usage_flag)
                                        except OSError:
                                            app_details['InstallLocationSize'] = "N/A (Access Error)"
                                    app_details['Remarks'] += " InstallLocation is a file;"
                                elif install_location_cleaned:
                                    app_details['PathStatus'] = "Path Not Found"
                                    app_details['Remarks'] += " Broken install path (Actionable);"
                                else:
                                    app_details['PathStatus'] = "No Valid Path in Registry"
                                    if app_details['Category'] == "Application":
                                        app_details['Remarks'] += " Registry entry only (Potential Orphan?). Consider searching common install locations (e.g., Program Files) for remnants if software is unexpected.;"
                            except FileNotFoundError:
                                app_details['InstallLocation'] = "N/A"
                                app_details['PathStatus'] = "No Path in Registry"
                                if app_details['Category'] == "Application":
                                     app_details['Remarks'] += " Registry entry only (Potential Orphan?). Consider searching common install locations (e.g., Program Files) for remnants if software is unexpected.;"
                            except OSError as e:
                                app_details['InstallLocation'] = f"Path Read Error: {e.strerror}"
                                app_details['PathStatus'] = "Error"
                                app_details['Remarks'] += f" Error accessing install path: {e.strerror};"

                            current_remarks = app_details['Remarks'].strip().strip(';')
                            added_launcher_remark = False
                            publisher_lower = str(app_details.get('Publisher', '')).lower()
                            location_lower = str(app_details.get('InstallLocation', '')).lower()
                            for remark_text, hints in LAUNCHER_HINTS.items():
                                matched_hint = False
                                if "publishers" in hints:
                                    for p_hint in hints["publishers"]:
                                        if p_hint in publisher_lower:
                                            current_remarks = (current_remarks + f" {remark_text}" if current_remarks else remark_text).strip()
                                            matched_hint = True
                                            added_launcher_remark = True
                                            break
                                if matched_hint: break
                                if "paths" in hints:
                                    for path_hint in hints["paths"]:
                                        if path_hint in location_lower:
                                            current_remarks = (current_remarks + f" {remark_text}" if current_remarks else remark_text).strip()
                                            matched_hint = True
                                            added_launcher_remark = True
                                            break
                                if matched_hint: break
                            app_details['Remarks'] = current_remarks

                            if app_details['Category'] == "Component/Driver" and app_details['PathStatus'] in ["No Path in Registry", "No Valid Path in Registry"]:
                                if not added_launcher_remark and "Component" not in app_details['Remarks']:
                                     app_details['Remarks'] = (app_details['Remarks'].strip() + " Component (no specific path).").strip()

                            app_details['Remarks'] = app_details['Remarks'].strip(';')

                            if app_details['DisplayName'] and not app_details['DisplayName'].startswith('{'):
                                software_list.append(app_details)
                    except OSError:
                        pass
                    except Exception:
                        pass
        except FileNotFoundError:
            print(f"Registry path not found: {hive_display_name} - {path_suffix}. This might be normal.")
            continue
        except Exception as e_outer:
            print(f"An error occurred accessing registry path {hive_display_name} - {path_suffix}: {e_outer}")
            continue

    return sorted(software_list, key=lambda x: str(x.get('DisplayName','')).lower())

def output_to_json_combined(system_inventory_data, devenv_components_data, devenv_env_vars_data, devenv_issues_data, output_dir, filename="system_sage_combined_report.json"):
    combined_data = {}
    if system_inventory_data:
        combined_data["systemInventory"] = system_inventory_data

    if devenv_components_data or devenv_env_vars_data or devenv_issues_data:
        devenv_audit_data = {}
        if devenv_components_data:
            devenv_audit_data["detectedComponents"] = [comp.to_dict() for comp in devenv_components_data]
        if devenv_env_vars_data:
            devenv_audit_data["environmentVariables"] = [ev.to_dict() for ev in devenv_env_vars_data]
        if devenv_issues_data:
            devenv_audit_data["identifiedIssues"] = [issue.to_dict() for issue in devenv_issues_data]
        if devenv_audit_data: # only add if there's something
             combined_data["devEnvAudit"] = devenv_audit_data

    if not combined_data:
        logging.info("No data to save to JSON report.")
        return

    try:
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Combined JSON report successfully saved to {full_path}") # Changed print to logging
    except Exception as e:
        logging.error(f"Error saving combined JSON file to {output_dir}: {e}") # Changed print to logging
        raise # Re-raise for the GUI to catch and show via messagebox

def output_to_markdown_combined(system_inventory_data, devenv_components_data, devenv_env_vars_data, devenv_issues_data, output_dir, filename="system_sage_combined_report.md", include_system_sage_components_flag=True):
    try:
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"# System Sage Combined Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # --- System Inventory Section ---
            f.write("## System Software Inventory\n\n")
            if system_inventory_data:
                header = "| Application Name | Version | Publisher | Install Path | Size | Status | Remarks | Source Hive | Registry Key Path |\n"
                separator = "|---|---|---|---|---|---|---|---|---|\n"

                f.write("### Applications\n")
                f.write(header)
                f.write(separator)
                app_count = 0
                for app in system_inventory_data:
                    if app.get('Category') == "Application":
                        app_count +=1
                        name = str(app.get('DisplayName', 'N/A')).replace('|', '\\|')
                        version = str(app.get('DisplayVersion', 'N/A')).replace('|', '\\|')
                        publisher = str(app.get('Publisher', 'N/A')).replace('|', '\\|')
                        location = str(app.get('InstallLocation', 'N/A')).replace('|', '\\|')
                        size = str(app.get('InstallLocationSize', 'N/A')).replace('|', '\\|')
                        status = str(app.get('PathStatus', 'N/A')).replace('|', '\\|')
                        remarks = str(app.get('Remarks', '')).replace('|', '\\|')
                        hive = str(app.get('SourceHive', 'N/A')).replace('|', '\\|')
                        reg_key = str(app.get('RegistryKeyPath', 'N/A')).replace('|', '\\|')
                        f.write(f"| {name} | {version} | {publisher} | {location} | {size} | {status} | {remarks} | {hive} | {reg_key} |\n")
                if app_count == 0:
                    f.write("| No primary applications found. | | | | | | | | |\n")

                if include_system_sage_components_flag: # This flag is for System Inventory components
                    f.write("\n### Components & Drivers (System Inventory)\n")
                    f.write(header.replace("Application Name", "Component Name"))
                    f.write(separator)
                    comp_count = 0
                    for app in system_inventory_data:
                        if app.get('Category') == "Component/Driver":
                            comp_count +=1
                            name = str(app.get('DisplayName', 'N/A')).replace('|', '\\|')
                            version = str(app.get('DisplayVersion', 'N/A')).replace('|', '\\|')
                            publisher = str(app.get('Publisher', 'N/A')).replace('|', '\\|')
                            location = str(app.get('InstallLocation', 'N/A')).replace('|', '\\|')
                            size = str(app.get('InstallLocationSize', 'N/A')).replace('|', '\\|')
                            status = str(app.get('PathStatus', 'N/A')).replace('|', '\\|')
                            remarks = str(app.get('Remarks', '')).replace('|', '\\|')
                            hive = str(app.get('SourceHive', 'N/A')).replace('|', '\\|')
                            reg_key = str(app.get('RegistryKeyPath', 'N/A')).replace('|', '\\|')
                            f.write(f"| {name} | {version} | {publisher} | {location} | {size} | {status} | {remarks} | {hive} | {reg_key} |\n")
                    if comp_count == 0:
                         f.write("| No components/drivers found or filtering disabled. | | | | | | | | |\n")
            else:
                f.write("No System Inventory data available.\n")

            # --- DevEnvAudit Section ---
            f.write("\n## Developer Environment Audit Results\n")
            if devenv_components_data or devenv_env_vars_data or devenv_issues_data:
                if devenv_components_data:
                    f.write("\n### Detected Development Components\n")
                    comp_header = "| Name | Version | Category | Path | Executable Path | ID |\n"
                    comp_separator = "|---|---|---|---|---|---|\n"
                    f.write(comp_header)
                    f.write(comp_separator)
                    for comp in devenv_components_data: # Using .to_dict() is for JSON, here access attributes directly
                        name = str(comp.name).replace('|', '\\|')
                        version = str(comp.version).replace('|', '\\|')
                        category = str(comp.category).replace('|', '\\|')
                        path = str(comp.path if comp.path else "N/A").replace('|', '\\|')
                        exe_path = str(comp.executable_path if comp.executable_path else "N/A").replace('|', '\\|')
                        comp_id = str(comp.id).replace('|', '\\|')
                        f.write(f"| {name} | {version} | {category} | {path} | {exe_path} | {comp_id} |\n")
                    if not devenv_components_data: f.write("| No development components detected. | | | | | |\n")

                if devenv_env_vars_data:
                    f.write("\n### Key Environment Variables\n")
                    env_header = "| Name | Value | Scope |\n"
                    env_separator = "|---|---|---|\n"
                    f.write(env_header)
                    f.write(env_separator)
                    for ev in devenv_env_vars_data: # Using .to_dict() is for JSON
                        name = str(ev.name).replace('|', '\\|')
                        value = str(ev.value).replace('|', '\\|')
                        scope = str(ev.scope).replace('|', '\\|')
                        f.write(f"| {name} | {value} | {scope} |\n")
                    if not devenv_env_vars_data: f.write("| No environment variables data. | | |\n")

                if devenv_issues_data:
                    f.write("\n### Identified Issues (DevEnvAudit)\n")
                    issue_header = "| Severity | Description | Category | Component ID | Related Path |\n"
                    issue_separator = "|---|---|---|---|---|\n"
                    f.write(issue_header)
                    f.write(issue_separator)
                    for issue in devenv_issues_data: # Using .to_dict() is for JSON
                        severity = str(issue.severity).replace('|', '\\|')
                        desc = str(issue.description).replace('|', '\\|')
                        cat = str(issue.category).replace('|', '\\|')
                        comp_id_val = issue.component_id if issue.component_id is not None else "N/A"
                        rel_path_val = issue.related_path if issue.related_path is not None else "N/A"
                        comp_id = str(comp_id_val).replace('|', '\\|')
                        rel_path = str(rel_path_val).replace('|', '\\|')
                        f.write(f"| {severity} | {desc} | {cat} | {comp_id} | {rel_path} |\n")
                    if not devenv_issues_data: f.write("| No issues identified by DevEnvAudit. | | | | |\n")
            else:
                f.write("No Developer Environment Audit data available.\n")

            f.write("\n## Future Interactive Features (Planned)\n") # This section can remain as is or be updated
            f.write("The following features are planned for future versions of System Sage to allow for interactive management:\n\n")
            f.write("- **Orphaned Entry Review:** For items marked with 'Potential Orphan?' or 'Registry entry only?', System Sage will offer an option to:\n")
            f.write("  - Attempt to locate related files/folders on disk (potentially using an external search tool if available).\n")
            f.write("  - View detailed registry information.\n")
            f.write("  - (With explicit user confirmation) Securely back up and then delete the selected registry key.\n")
            f.write("- **Broken Path Resolution:** For items with 'Broken install path':\n")
            f.write("  - Allow the user to browse and select the correct installation path.\n")
            f.write("  - (With explicit user confirmation) Update the 'InstallLocation' value in the registry.\n")
            f.write("- **Advanced Filtering & Sorting:** More options to filter and sort the displayed/reported software list based on various criteria (e.g., disk size, last used - if discoverable, category).\n")
            f.write("- **Batch Actions:** For multiple selected items (e.g., multiple confirmed orphans), allow for batch processing of actions like registry key deletion (with appropriate safeguards and confirmations).\n\n")
            f.write("*Disclaimer: Modifying the Windows Registry carries risks. Future interactive features will be designed with safety and user confirmation as top priorities. Always ensure you have backups before making significant system changes.*\n")

        logging.info(f"Combined Markdown report successfully saved to {full_path}") # Changed print to logging
    except Exception as e:
        logging.error(f"Error saving combined Markdown file to {output_dir}: {e}") # Changed print to logging
        raise # Re-raise for the GUI to catch and show via messagebox


def run_devenv_audit():
    print("\n" + "=" * 40)
    print("--- Starting Developer Environment Audit ---")

    # Define simple console callbacks for DevEnvAudit
    def devenv_status_callback(message):
        print(f"[DevEnvAudit Status] {message}")

    def devenv_progress_callback(current, total, message):
        print(f"[DevEnvAudit Progress] {current}/{total}: {message}")

    try:
        # Ensure DevEnvAudit's config directory and default config file exist if its modules expect them.
        # The modified config_manager in devenvaudit_src should now use devenvaudit_src/devenvaudit_config.json
        # So, we just need to ensure that file is present. It was part of the bundled files.

        # Instantiate the scanner
        # Note: DevEnvAudit's EnvironmentScanner loads its own config via its config_manager.
        # We are not explicitly passing a config here, relying on the bundled devenvaudit_config.json.
        scanner = EnvironmentScanner(progress_callback=devenv_progress_callback, status_callback=devenv_status_callback)

        print("Running DevEnvAudit scan...")
        components, env_vars, issues = scanner.run_scan()

        print("\n--- DevEnvAudit Summary ---")
        print(f"Detected Software Components: {len(components)}")
        print(f"Collected Environment Variables: {len(env_vars)}")
        print(f"Identified Issues: {len(issues)}")

        if components:
            print("\nTop Detected Components (DevEnvAudit):")
            for i, comp in enumerate(components[:5]): # Print top 5
                print(f"  - {comp.name} ({comp.version or 'N/A'}) at {comp.path or 'N/A'}")
                if i == 4 and len(components) > 5:
                    print("    ...and more.")

        if issues:
            print("\nTop Issues (DevEnvAudit):")
            for i, issue in enumerate(issues[:5]): # Print top 5
                print(f"  - [{issue.severity}] {issue.description} (Category: {issue.category}, Component: {issue.component_id})")
                if i == 4 and len(issues) > 5:
                    print("    ...and more.")

    except ImportError as e:
        print(f"ERROR: Could not import DevEnvAudit modules: {e}")
        print("Please ensure 'devenvaudit_src' directory is present and contains the necessary files.")
    except FileNotFoundError as e:
        print(f"ERROR: DevEnvAudit required file not found: {e}")
        print("This might be 'devenvaudit_config.json' or 'software categorization database.json' or 'tools_database.json' in 'devenvaudit_src'.")
    except Exception as e:
        print(f"An unexpected error occurred during the Developer Environment Audit: {e}")
        logging.exception("DevEnvAudit execution failed") # Log full traceback

    print("--- Developer Environment Audit Finished ---")
    print("=" * 40)

class SystemSageApp(tk.Tk):
    def __init__(self, cli_args=None): # Accept cli_args
        super().__init__()
        self.cli_args = cli_args # Store them
        self.inventory_tree = None
        self.scan_in_progress = False
        # Result storage attributes
        self.system_inventory_results = []
        self.devenv_components_results = []
        self.devenv_env_vars_results = []
        self.devenv_issues_results = []
        # DevEnvAudit Treeviews
        self.devenv_components_tree = None
        self.devenv_env_vars_tree = None
        self.devenv_issues_tree = None
        # OCL UI Elements
        self.ocl_profiles_tree = None
        self.ocl_profile_details_text = None
        self.ocl_refresh_button = None
        self.ocl_save_new_button = None
        self.ocl_update_selected_button = None

        self.title("System Sage")
        self.geometry("1200x800") # Adjusted size for more content

        # --- Menu Bar ---
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Save Combined Report (JSON & MD)", command=self.save_combined_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Scan Menu
        self.scan_menu = tk.Menu(self.menu_bar, tearoff=0) # Store as self.scan_menu
        self.scan_menu.add_command(label="Run System Inventory Scan", command=self.start_system_inventory_scan)
        self.scan_menu.add_command(label="Run DevEnv Audit", command=self.start_devenv_audit_scan) # Updated command
        self.menu_bar.add_cascade(label="Scan", menu=self.scan_menu)

        # --- Main Content Area ---
        main_notebook = ttk.Notebook(self) # Use a Notebook for tabs
        main_notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Tab 1: System Inventory
        inventory_tab = ttk.Frame(main_notebook)
        main_notebook.add(inventory_tab, text="System Inventory")

        columns = ("Name", "Version", "Publisher", "Path", "Size", "Status", "Remarks", "SourceHive", "RegKey")
        self.inventory_tree = ttk.Treeview(inventory_tab, columns=columns, show="headings")

        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=100, anchor=tk.W) # Adjust widths as needed
            if col == "Name": self.inventory_tree.column(col, width=200)
            if col == "Path": self.inventory_tree.column(col, width=250)
            if col == "RegKey": self.inventory_tree.column(col, width=250)


        # Scrollbars
        vsb = ttk.Scrollbar(inventory_tab, orient="vertical", command=self.inventory_tree.yview)
        hsb = ttk.Scrollbar(inventory_tab, orient="horizontal", command=self.inventory_tree.xview)
        self.inventory_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.inventory_tree.pack(expand=True, fill=tk.BOTH)

        # Tab 2: DevEnv Audit
        devenv_tab = ttk.Frame(main_notebook)
        main_notebook.add(devenv_tab, text="Developer Environment Audit")

        # Create Labelframes for each section, packed vertically
        components_frame = ttk.Labelframe(devenv_tab, text="Detected Components")
        components_frame.pack(padx=5, pady=5, fill="both", expand=True)

        env_vars_frame = ttk.Labelframe(devenv_tab, text="Environment Variables")
        env_vars_frame.pack(padx=5, pady=5, fill="both", expand=True)

        issues_frame = ttk.Labelframe(devenv_tab, text="Identified Issues")
        issues_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # Components Treeview
        comp_cols = ("ID", "Name", "Category", "Version", "Path", "Executable Path")
        self.devenv_components_tree = ttk.Treeview(components_frame, columns=comp_cols, show="headings")
        for col in comp_cols:
            self.devenv_components_tree.heading(col, text=col)
            self.devenv_components_tree.column(col, width=150, anchor=tk.W) # Adjust as needed
        comp_vsb = ttk.Scrollbar(components_frame, orient="vertical", command=self.devenv_components_tree.yview)
        comp_hsb = ttk.Scrollbar(components_frame, orient="horizontal", command=self.devenv_components_tree.xview)
        self.devenv_components_tree.configure(yscrollcommand=comp_vsb.set, xscrollcommand=comp_hsb.set)
        comp_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        comp_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.devenv_components_tree.pack(expand=True, fill=tk.BOTH)

        # Environment Variables Treeview
        env_cols = ("Name", "Value", "Scope")
        self.devenv_env_vars_tree = ttk.Treeview(env_vars_frame, columns=env_cols, show="headings")
        for col in env_cols:
            self.devenv_env_vars_tree.heading(col, text=col)
            self.devenv_env_vars_tree.column(col, width=200, anchor=tk.W)
        env_vsb = ttk.Scrollbar(env_vars_frame, orient="vertical", command=self.devenv_env_vars_tree.yview)
        env_hsb = ttk.Scrollbar(env_vars_frame, orient="horizontal", command=self.devenv_env_vars_tree.xview)
        self.devenv_env_vars_tree.configure(yscrollcommand=env_vsb.set, xscrollcommand=env_hsb.set)
        env_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        env_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.devenv_env_vars_tree.pack(expand=True, fill=tk.BOTH)

        # Issues Treeview
        issue_cols = ("Severity", "Description", "Category", "Component ID", "Related Path")
        self.devenv_issues_tree = ttk.Treeview(issues_frame, columns=issue_cols, show="headings")
        for col in issue_cols:
            self.devenv_issues_tree.heading(col, text=col)
            self.devenv_issues_tree.column(col, width=150, anchor=tk.W)
            if col == "Description": self.devenv_issues_tree.column(col, width=300)
        issue_vsb = ttk.Scrollbar(issues_frame, orient="vertical", command=self.devenv_issues_tree.yview)
        issue_hsb = ttk.Scrollbar(issues_frame, orient="horizontal", command=self.devenv_issues_tree.xview)
        self.devenv_issues_tree.configure(yscrollcommand=issue_vsb.set, xscrollcommand=issue_hsb.set)
        issue_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        issue_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.devenv_issues_tree.pack(expand=True, fill=tk.BOTH)

        # Tab 3: Overclocker's Logbook (OCL)
        ocl_tab = ttk.Frame(main_notebook)
        main_notebook.add(ocl_tab, text="Overclocker's Logbook")

        # Main paned window for OCL tab (top: list, bottom: details+actions)
        ocl_paned_window = ttk.PanedWindow(ocl_tab, orient=tk.VERTICAL)
        ocl_paned_window.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # --- Top Pane: Profile List ---
        profiles_list_outer_frame = ttk.Labelframe(ocl_paned_window, text="Available Overclocking Profiles")
        ocl_paned_window.add(profiles_list_outer_frame, weight=1)

        # Frame to hold treeview and its scrollbar for better packing
        profiles_list_tree_frame = ttk.Frame(profiles_list_outer_frame)
        profiles_list_tree_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        ocl_profile_columns = ("ID", "Profile Name", "Last Modified")
        self.ocl_profiles_tree = ttk.Treeview(profiles_list_tree_frame, columns=ocl_profile_columns, show="headings")
        self.ocl_profiles_tree.heading("ID", text="ID")
        self.ocl_profiles_tree.column("ID", width=50, anchor=tk.W, stretch=tk.NO) # ID column not stretchy
        self.ocl_profiles_tree.heading("Profile Name", text="Profile Name")
        self.ocl_profiles_tree.column("Profile Name", width=250, anchor=tk.W)
        self.ocl_profiles_tree.heading("Last Modified", text="Last Modified")
        self.ocl_profiles_tree.column("Last Modified", width=150, anchor=tk.W)

        ocl_profiles_vsb = ttk.Scrollbar(profiles_list_tree_frame, orient="vertical", command=self.ocl_profiles_tree.yview)
        self.ocl_profiles_tree.configure(yscrollcommand=ocl_profiles_vsb.set)

        self.ocl_profiles_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        ocl_profiles_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.ocl_profiles_tree.bind("<<TreeviewSelect>>", self.on_ocl_profile_select)

        # --- Bottom Pane: Details & Actions ---
        details_actions_frame = ttk.Frame(ocl_paned_window)
        ocl_paned_window.add(details_actions_frame, weight=2)

        # Details Sub-Frame
        profile_details_frame = ttk.Labelframe(details_actions_frame, text="Profile Details")
        profile_details_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=(0,5), side=tk.TOP) # Add some padding

        self.ocl_profile_details_text = tk.Text(profile_details_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        ocl_details_vsb = ttk.Scrollbar(profile_details_frame, orient="vertical", command=self.ocl_profile_details_text.yview)
        self.ocl_profile_details_text.configure(yscrollcommand=ocl_details_vsb.set)

        self.ocl_profile_details_text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(5,0), pady=5)
        ocl_details_vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)


        # Actions Sub-Frame
        actions_frame = ttk.Frame(details_actions_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)

        self.ocl_refresh_button = ttk.Button(actions_frame, text="Refresh Profile List", command=self.refresh_ocl_profiles_list)
        self.ocl_refresh_button.pack(side=tk.LEFT, padx=2)

        self.ocl_save_new_button = ttk.Button(actions_frame, text="Save System as New Profile", command=self.save_system_as_new_ocl_profile)
        self.ocl_save_new_button.pack(side=tk.LEFT, padx=2)

        self.ocl_update_selected_button = ttk.Button(actions_frame, text="Update Selected Profile", command=self.update_selected_ocl_profile)
        self.ocl_update_selected_button.pack(side=tk.LEFT, padx=2)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_system_inventory_scan(self):
        if self.scan_in_progress:
            messagebox.showwarning("Scan In Progress", "A scan is already running. Please wait.")
            return

        self.scan_in_progress = True
        self.status_bar.config(text="Starting System Inventory Scan...")
        self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.DISABLED)
        self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.DISABLED)

        if self.inventory_tree:
            for i in self.inventory_tree.get_children():
                self.inventory_tree.delete(i)

        calc_disk_usage = True
        if self.cli_args and hasattr(self.cli_args, 'calculate_disk_usage'):
             calc_disk_usage = self.cli_args.calculate_disk_usage

        thread = Thread(target=self.run_system_inventory_thread, args=(calc_disk_usage,), daemon=True)
        thread.start()

    def run_system_inventory_thread(self, calculate_disk_usage_flag):
        try:
            software_list = get_installed_software(calculate_disk_usage_flag) # Global function
            self.after(0, self.update_inventory_display, software_list)
        except Exception as e:
            tb_str = traceback.format_exc()
            logging.error(f"Error in system inventory thread: {e}\n{tb_str}")
            self.after(0, self.inventory_scan_error, e)

    def update_inventory_display(self, software_list):
        if self.inventory_tree:
            for app in software_list:
                self.inventory_tree.insert("", tk.END, values=(
                    app.get('DisplayName', 'N/A'),
                    app.get('DisplayVersion', 'N/A'),
                    app.get('Publisher', 'N/A'),
                    app.get('InstallLocation', 'N/A'),
                    app.get('InstallLocationSize', 'N/A'),
                    app.get('PathStatus', 'N/A'),
                    app.get('Remarks', ''),
                    app.get('SourceHive', 'N/A'),
                    app.get('RegistryKeyPath', 'N/A')
                ))

        self.system_inventory_results = software_list # Store results
        self.status_bar.config(text=f"System Inventory Scan Complete. Found {len(software_list)} items.")
        self.scan_in_progress = False
        self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.NORMAL)
        self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.NORMAL)

    def inventory_scan_error(self, error):
        messagebox.showerror("Scan Error", f"An error occurred during the System Inventory Scan: {error}")
        self.status_bar.config(text="System Inventory Scan Failed.")
        self.scan_in_progress = False
        self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.NORMAL)
        self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.NORMAL)

    # --- DevEnvAudit Methods (Relocated and adapted) ---
    def _devenv_status_callback(self, message): # Renamed and made instance method
        # This could update a status bar or a specific label in the DevEnv tab
        self.status_bar.config(text=f"[DevEnvAudit] {message}")
        logging.info(f"[DevEnvAudit Status] {message}")


    def _devenv_progress_callback(self, current, total, message): # Renamed and made instance method
        # This could update a progress bar in the DevEnv tab
        self.status_bar.config(text=f"[DevEnvAudit Progress] {current}/{total}: {message}")
        logging.info(f"[DevEnvAudit Progress] {current}/{total}: {message}")

    def start_devenv_audit_scan(self): # Renamed from run_devenv_audit
        if self.scan_in_progress:
            messagebox.showwarning("Scan In Progress", "A scan is already running. Please wait.")
            return

        self.scan_in_progress = True
        self.status_bar.config(text="Starting Developer Environment Audit...")
        self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.DISABLED)
        self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.DISABLED)

        # Placeholder: Clear previous DevEnv results if UI elements exist
        # e.g., self.devenv_results_text.delete('1.0', tk.END)

        thread = Thread(target=self.run_devenv_audit_thread, daemon=True)
        thread.start()

    def run_devenv_audit_thread(self):
        try:
            scanner = EnvironmentScanner(progress_callback=self._devenv_progress_callback,
                                         status_callback=self._devenv_status_callback)
            components, env_vars, issues = scanner.run_scan()

            # For now, log results. GUI display for DevEnvAudit is future.
            logging.info("--- DevEnvAudit Summary (from GUI thread) ---")
            logging.info(f"Detected Software Components: {len(components)}")
            logging.info(f"Collected Environment Variables: {len(env_vars)}")
            logging.info(f"Identified Issues: {len(issues)}")

            self.after(0, self.update_devenv_audit_display, components, env_vars, issues)

        except ImportError as e:
            logging.error(f"ERROR: Could not import DevEnvAudit modules: {e}")
            self.after(0, self.devenv_scan_error, e)
        except FileNotFoundError as e:
            logging.error(f"ERROR: DevEnvAudit required file not found: {e}")
            self.after(0, self.devenv_scan_error, e)
        except Exception as e:
            tb_str = traceback.format_exc()
            logging.error(f"An unexpected error occurred during the Developer Environment Audit: {e}\n{tb_str}")
            self.after(0, self.devenv_scan_error, e)
        # Removed finally block as finalize_devenv_scan is called by update_devenv_audit_display and devenv_scan_error

    def update_devenv_audit_display(self, components, env_vars, issues):
        # Clear previous results
        for tree in [self.devenv_components_tree, self.devenv_env_vars_tree, self.devenv_issues_tree]:
            if tree:
                for i in tree.get_children():
                    tree.delete(i)

        # Populate Components Tree
        if self.devenv_components_tree:
            for comp in components:
                self.devenv_components_tree.insert("", tk.END, values=(
                    comp.id, comp.name, comp.category, comp.version, comp.path, comp.executable_path
                ))

        # Populate Environment Variables Tree
        if self.devenv_env_vars_tree:
            for ev in env_vars:
                self.devenv_env_vars_tree.insert("", tk.END, values=(
                    ev.name, ev.value, ev.scope
                ))

        # Populate Issues Tree
        if self.devenv_issues_tree:
            for issue in issues:
                self.devenv_issues_tree.insert("", tk.END, values=(
                    issue.severity, issue.description, issue.category, issue.component_id, issue.related_path
                ))

        self.devenv_components_results = components
        self.devenv_env_vars_results = env_vars
        self.devenv_issues_results = issues
        self.finalize_devenv_scan(message=f"DevEnv Audit Complete. Found {len(components)} components, {len(env_vars)} env vars, {len(issues)} issues.")

    def devenv_scan_error(self, error):
        messagebox.showerror("DevEnv Audit Error", f"An error occurred during the Developer Environment Audit: {error}")
        self.finalize_devenv_scan(message="DevEnv Audit Failed.")

    def finalize_devenv_scan(self, message="DevEnv Audit Finished."):
        self.status_bar.config(text=message)
        self.scan_in_progress = False
        self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.NORMAL)
        self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.NORMAL)

    def save_combined_report(self):
        if not self.system_inventory_results and not self.devenv_components_results:
            messagebox.showwarning("No Data", "No scan data available to save. Please run a scan first.")
            return

        output_dir_default = DEFAULT_OUTPUT_DIR # Use the global default
        if self.cli_args and self.cli_args.output_dir:
            output_dir_default = self.cli_args.output_dir

        output_dir = filedialog.askdirectory(initialdir=output_dir_default, title="Select Output Directory for Reports")

        if not output_dir: # User cancelled
            return

        try:
            # Determine if System Sage components should be included in Markdown based on CLI args or a default
            md_include_components = DEFAULT_MARKDOWN_INCLUDE_COMPONENTS # Default from global
            if self.cli_args: # Check if CLI args were even parsed
                if hasattr(self.cli_args, 'markdown_include_components_flag') and self.cli_args.markdown_include_components_flag:
                    md_include_components = True
                elif hasattr(self.cli_args, 'markdown_no_components_flag') and self.cli_args.markdown_no_components_flag:
                    md_include_components = False

            # Call the modified global output functions
            output_to_json_combined(
                self.system_inventory_results,
                self.devenv_components_results,
                self.devenv_env_vars_results,
                self.devenv_issues_results,
                output_dir
            )
            output_to_markdown_combined(
                self.system_inventory_results,
                self.devenv_components_results,
                self.devenv_env_vars_results,
                self.devenv_issues_results,
                output_dir,
                include_system_sage_components_flag=md_include_components
            )
            messagebox.showinfo("Reports Saved", f"Combined JSON and Markdown reports saved to: {output_dir}")
        except Exception as e:
            logging.error(f"Error saving reports: {e}\n{traceback.format_exc()}")
            messagebox.showerror("Save Error", f"Failed to save reports: {e}")

    def quit_app(self):
        if self.scan_in_progress:
            if messagebox.askyesno("Scan in Progress", "A scan is currently in progress. Exiting now might lose unsaved data or leave processes unfinished. Do you really want to exit?"):
                # Add any necessary cleanup for ongoing threads if possible, though daemon threads will exit
                self.destroy()
            else:
                return # Do not exit
        elif messagebox.askokcancel("Quit", "Do you really want to exit System Sage?"):
            self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="System Sage - Software Inventory and Path Validator.")
    parser.add_argument(
        "--no-disk-usage",
        action="store_false",
        dest="calculate_disk_usage",
        default=DEFAULT_CALCULATE_DISK_USAGE,
        help="Disable disk usage calculation for a faster scan."
    )
    parser.add_argument(
        "--no-json",
        action="store_false",
        dest="output_json",
        default=DEFAULT_OUTPUT_JSON,
        help="Disable JSON file output."
    )
    parser.add_argument(
        "--no-markdown",
        action="store_false",
        dest="output_markdown",
        default=DEFAULT_OUTPUT_MARKDOWN,
        help="Disable Markdown file output."
    )
    # V1.2: Added argument for output directory
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Specify the directory for output files (default: {DEFAULT_OUTPUT_DIR})."
    )
    parser.add_argument(
        "--md-include-components",
        action="store_true",
        dest="markdown_include_components_flag",
        help="Explicitly include components/drivers in the Markdown report."
    )
    parser.add_argument(
        "--md-no-components",
        action="store_true",
        dest="markdown_no_components_flag",
        help="Explicitly exclude components/drivers from the Markdown report (overrides default)."
    )
    parser.add_argument(
        "--console-include-components",
        action="store_true",
        dest="console_include_components_flag",
        help="Explicitly include components/drivers in the console output."
    )
    parser.add_argument(
        "--console-no-components",
        action="store_true",
        dest="console_no_components_flag",
        help="Explicitly exclude components/drivers from the console output (overrides default)."
    )
    parser.add_argument(
        "--run-devenv-audit",
        action="store_true",
        dest="run_devenv_audit_flag", # Give it a distinct dest name
        default=False, # Ensure it defaults to False
        help="Run the Developer Environment Audit in addition to the software inventory."
    )

    args = parser.parse_args() # This line is still needed

    # --- GUI LAUNCH ---
    # Basic logging setup for the GUI application itself (can be refined)
    # Check if logging is already configured (e.g. by another module)
    if not logging.getLogger().hasHandlers(): # Check if root logger has handlers
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    try:
        app = SystemSageApp(cli_args=args) # Pass CLI args to the app
        app.mainloop()
    except Exception as e:
        logging.critical("GUI Crashed: %s", e, exc_info=True)
        # Fallback to a simple Tkinter error message if mainloop fails catastrophically
        try:
            root = tk.Tk()
            root.withdraw() # Hide the main Tk window
            messagebox.showerror("Fatal GUI Error", f"A critical error occurred: {e}\nSee logs for details if logging was active.")
            root.destroy()
        except Exception as critical_e:
            print(f"CRITICAL FALLBACK ERROR: {critical_e}") # Last resort print
    # --- END GUI LAUNCH ---
