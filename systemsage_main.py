# System Sage - Integrated System Utility V2.5
# This script provides system inventory, developer environment auditing,
# and other utilities.
# V2.5:
# - Renamed to systemsage_main.py
# placeholder for more detailed description
# - Added custom message box function for better user feedback


import os
import platform
import json
import datetime
import argparse
import tkinter as tk
from threading import Thread
import traceback
import sys
import logging
import customtkinter
from CTkTable import CTkTable
# CTkFileDialog will be imported in the fallback logic below
from tkinter import messagebox # Import messagebox explicitly

# --- DevEnvAudit Imports ---
from devenvaudit_src.scan_logic import EnvironmentScanner
from devenvaudit_src.report_generator import ReportGenerator

# --- OCL Module Imports ---
from ocl_module_src import olb_api as ocl_api
# --- NEW: Import the new OCL Profile Editor and data structures ---
from ocl_module_src.bios_profile import Profile, load_from_json_file
from ocl_module_src.profile_editor_ui import OclProfileEditor

# --- Custom Message Box Function (defined before CTkFileDialog placeholder that might use it) ---
def show_custom_messagebox(parent_window, title, message, dialog_type="info"):
    """
    Displays a custom modal dialog box using CustomTkinter.
    parent_window: The parent window for the dialog (usually self of the App class).
    title: The title of the dialog window.
    message: The message to display in the dialog.
    dialog_type: "info", "warning", or "error". Can be used for theming/icons in future.
    """
    dialog = customtkinter.CTkToplevel(parent_window)

    title_prefix = ""
    if dialog_type == "error":
        title_prefix = "Error: "
    elif dialog_type == "warning":
        title_prefix = "Warning: "
    dialog.title(title_prefix + title)

    dialog.transient(parent_window)
    dialog.attributes("-topmost", True)
    dialog.resizable(
        False, False
    )  # Prevent manual resizing which can look odd with auto-sizing

    # Determine a reasonable max width for the dialog based on parent, default to a sensible value
    parent_width_for_calc = (
        parent_window.winfo_width() if parent_window.winfo_viewable() else 800
    )
    max_dialog_width = max(
        350, parent_width_for_calc - 100
    )  # Ensure some padding from parent edges

    frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    frame.pack(
        expand=True, fill="both", padx=15, pady=15
    )  # Increased padding for better aesthetics

    # Label for the message, set wraplength to control width and allow height to adjust
    # Wraplength is crucial for auto-sizing based on text content.
    label = customtkinter.CTkLabel(
        frame, text=message, wraplength=max_dialog_width - 60, justify="left"
    )  # Adjusted wraplength considering frame padding
    label.pack(
        padx=10, pady=(0, 15), expand=True, fill="x"
    )  # Fill x, allow y to be determined by text

    ok_button = customtkinter.CTkButton(
        frame, text="OK", command=dialog.destroy, width=100
    )
    ok_button.pack(pady=(0, 5), side="bottom")  # Reduced bottom padding for button

    # Update geometry to fit content
    dialog.update_idletasks()  # Ensure widgets have their sizes calculated

    # Get required width and height
    req_width = dialog.winfo_reqwidth()
    req_height = dialog.winfo_reqheight()

    # Cap the width to max_dialog_width and height to a portion of parent height
    final_width = min(req_width, max_dialog_width)
    parent_height_for_calc = (
        parent_window.winfo_height() if parent_window.winfo_viewable() else 600
    )
    max_dialog_height = parent_height_for_calc - 100
    final_height = min(req_height, max_dialog_height)

    # Center the dialog on the parent window
    if parent_window.winfo_viewable():
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()

        # Calculate x and y for centering
        x = parent_x + (parent_width // 2) - (final_width // 2)
        y = parent_y + (parent_height // 2) - (final_height // 2)

        dialog.geometry(f"{final_width}x{final_height}+{x}+{y}")
    else:
        # Fallback if parent is not viewable (e.g., during init)
        # Center on screen (this might need adjustment for multi-monitor setups)
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width // 2) - (final_width // 2)
        y = (screen_height // 2) - (final_height // 2)
        dialog.geometry(f"{final_width}x{final_height}+{x}+{y}")

    dialog.grab_set()
    dialog.wait_window()


# --- CTkFileDialog Import with Fallback ---
class _BaseCTkFileDialogPlaceholder:
    def __init__(
        self, master=None, title=None, open_folder=None, initialdir=None, **kwargs
    ):
        self.master = master
        self.title = title
        self.open_folder = open_folder
        self.initialdir = initialdir
        self.path = None  # Add path attribute to the placeholder
        log_msg = (
            "Placeholder CTkFileDialog instantiated. Real import might have failed."
        )
        logging.warning(log_msg)
        try:
            parent_window_for_msg = master
            temp_root_created = False
            if not parent_window_for_msg:
                parent_window_for_msg = customtkinter.CTk()
                parent_window_for_msg.withdraw()
                temp_root_created = True
            if parent_window_for_msg:
                show_custom_messagebox(
                    parent_window_for_msg,
                    "File Dialog Warning",
                    "File dialog (CTkFileDialog) may be using a placeholder due to an import issue. File selection might not work.",
                    dialog_type="warning",
                )
            if temp_root_created and parent_window_for_msg:
                parent_window_for_msg.destroy()
        except Exception as e_placeholder_msg:
            logging.error(
                f"Error showing placeholder CTkFileDialog message: {e_placeholder_msg}"
            )

    def get(self):
        logging.error("Placeholder CTkFileDialog.get() called. Returning None.")
        return self.path # Return self.path for consistency, though it will be None


CTkFileDialog = _BaseCTkFileDialogPlaceholder

try:
    # Attempt to import the class from the correct module within the package
    from CTkFileDialog.ctk_file_dialog import CTkFileDialog as RealCTkFileDialog

    # Ensure what we imported is actually callable (a class)
    if callable(RealCTkFileDialog):
        CTkFileDialog = RealCTkFileDialog
        logging.info(
            "Successfully imported real CTkFileDialog"
        )
    else:
        logging.warning(
            "Imported CTkFileDialog is not callable. Placeholder will be used."
        )
        # CTkFileDialog remains _BaseCTkFileDialogPlaceholder
except ImportError as e_import_ctk:
    logging.warning(
        f"Failed to import real CTkFileDialog: {e_import_ctk}. Placeholder will be used."
    )
except Exception as e_unexpected_import:
    logging.error(
        f"Unexpected error during CTkFileDialog import: {e_unexpected_import}. Placeholder will be used."
    )

# The following block was part of the original code structure, ensure logging matches.
# If the above try-except successfully assigns RealCTkFileDialog, this log is fine.
# If it falls through to placeholder, the previous logs cover it.
# The original log was:
# logging.info(
# "Successfully imported real CTkFileDialog from CTkFileDialog.CTkFileDialog"
# )
# This needs to be adjusted based on which import succeeded if we had multiple attempts.
# Given the simplification to one primary import attempt for the real dialog:
if CTkFileDialog is not _BaseCTkFileDialogPlaceholder:
    pass # Logging already handled if RealCTkFileDialog was assigned
else:
    # This case is logged by the except blocks or the 'not callable' path.
    pass


# --- Helper function for PyInstaller resource path ---
# --- Helper function for PyInstaller resource path ---
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# --- Platform Specific Setup ---
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import winreg
    except ImportError:
        logging.error(
            "Failed to import winreg on a Windows system. System Inventory will not work."
        )
        # Ensure winreg is None or a mock if import fails, to prevent unbound errors later
        winreg = None # type: ignore 
else:
    winreg = None # type: ignore

# --- Configuration Loading Function ---
def load_json_config(filename, default_data):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                logging.info(f"Successfully loaded configuration from {filename}")
                return data
        else:
            logging.warning(
                f"Configuration file {filename} not found. Using default values."
            )
    except json.JSONDecodeError as e:
        logging.error(
            f"Failed to load custom theme from {filename}: {e}. Using default dark-blue theme."
        )
    except Exception as e:
        logging.warning(
            f"Unexpected error loading {filename}: {e}. Using default values."
        )
    return default_data


DEFAULT_CALCULATE_DISK_USAGE = True
DEFAULT_OUTPUT_JSON = True
DEFAULT_OUTPUT_MARKDOWN = True
DEFAULT_MARKDOWN_INCLUDE_COMPONENTS = True
DEFAULT_CONSOLE_INCLUDE_COMPONENTS = False
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_COMPONENT_KEYWORDS = ["driver", "sdk", "runtime"]
DEFAULT_SOFTWARE_HINTS = resource_path("systemsage_software_hints.json")
COMPONENT_KEYWORDS_FILE = resource_path("systemsage_component_keywords.json")
SOFTWARE_HINTS_FILE = resource_path("systemsage_software_hints.json")
COMPONENT_KEYWORDS = load_json_config(
    COMPONENT_KEYWORDS_FILE, DEFAULT_COMPONENT_KEYWORDS
)
SOFTWARE_HINTS = load_json_config(SOFTWARE_HINTS_FILE, DEFAULT_SOFTWARE_HINTS)


class DirectorySizeError(Exception):
    pass


def is_likely_component(display_name, publisher):
    if not IS_WINDOWS:
        return False
    name_lower = str(display_name).lower()
    publisher_lower = str(publisher).lower()

    for keyword in COMPONENT_KEYWORDS:
        if keyword in name_lower or keyword in publisher_lower:
            return True
    if name_lower.startswith("{") or name_lower.startswith("kb"):
        return True
    return False


def get_hkey_name(hkey_root):
    """
    Returns the string name of a Windows registry hive constant.
    If the hive is unknown, returns 'UNKNOWN_HIVE'.
    """
    if not IS_WINDOWS or not winreg: # Added check for winreg
        return "N/A"
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
        raise DirectorySizeError(
            f"Error accessing directory {directory_path}: {e}"
        ) from e
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
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"


def get_installed_software(calculate_disk_usage_flag):
    if not IS_WINDOWS:
        logging.info(
            "System Inventory (registry scan) is skipped as it's only available on Windows."
        )
        return [
            {
                "DisplayName": "System Inventory",
                "Remarks": "System Inventory (via registry scan) is only available on Windows.",
                "Category": "Informational",
            }
        ]

    software_list = []
    processed_entries = set()
    registry_paths = [
        (
            winreg.HKEY_LOCAL_MACHINE, # type: ignore
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            "HKLM (64-bit)",
        ), 
        (
            winreg.HKEY_LOCAL_MACHINE, # type: ignore
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            "HKLM (32-bit)",
        ), 
        (
            winreg.HKEY_CURRENT_USER, # type: ignore 
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            "HKCU",
        ),
    ]  # type: ignore

    for hkey_root, path_suffix, hive_display_name in registry_paths:
        if not winreg: continue # Skip if winreg is not available
        try:
            with winreg.OpenKey(hkey_root, path_suffix) as uninstall_key:  # type: ignore
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]):  # type: ignore
                    subkey_name = ""
                    app_details = {}
                    full_reg_key_path = "N/A"
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)  # type: ignore
                        full_reg_key_path = (
                            f"{get_hkey_name(hkey_root)}\\{path_suffix}\\{subkey_name}"
                        )
                        with winreg.OpenKey(uninstall_key, subkey_name) as app_key:  # type: ignore
                            app_details = {
                                "SourceHive": hive_display_name,
                                "RegistryKeyPath": full_reg_key_path,
                                "InstallLocationSize": "N/A"
                                if calculate_disk_usage_flag
                                else "Not Calculated",
                                "Remarks": "",
                            }
                            try:
                                app_details["DisplayName"] = str(
                                    winreg.QueryValueEx(app_key, "DisplayName")[0]
                                )  # type: ignore
                            except FileNotFoundError:
                                app_details["DisplayName"] = subkey_name
                            except OSError as e:
                                app_details["DisplayName"] = (
                                    f"{subkey_name} (Name Error: {e.strerror})"
                                )
                            entry_id_name = app_details["DisplayName"]
                            entry_id_version = "N/A"
                            try:
                                app_details["DisplayVersion"] = str(
                                    winreg.QueryValueEx(app_key, "DisplayVersion")[0]
                                )
                                entry_id_version = app_details["DisplayVersion"]  # type: ignore
                            except FileNotFoundError:
                                app_details["DisplayVersion"] = "N/A"
                            except OSError as e:
                                app_details["DisplayVersion"] = (
                                    f"Version Error: {e.strerror}"
                                )
                            entry_id = (entry_id_name, entry_id_version)
                            if entry_id in processed_entries:
                                continue
                            processed_entries.add(entry_id)
                            try:
                                app_details["Publisher"] = str(
                                    winreg.QueryValueEx(app_key, "Publisher")[0]
                                )  # type: ignore
                            except FileNotFoundError:
                                app_details["Publisher"] = "N/A"
                            except OSError as e:
                                app_details["Publisher"] = (
                                    f"Publisher Error: {e.strerror}"
                                )
                            app_details["Category"] = (
                                "Component/Driver"
                                if is_likely_component(
                                    app_details["DisplayName"], app_details["Publisher"]
                                )
                                else "Application"
                            )
                            try:
                                install_location_raw = winreg.QueryValueEx(
                                    app_key, "InstallLocation"
                                )[0]
                                install_location_cleaned = str(install_location_raw)  # type: ignore
                                if isinstance(install_location_raw, str):
                                    temp_location = install_location_raw.strip()
                                    if (
                                        temp_location.startswith('"')
                                        and temp_location.endswith('"')
                                    ) or (
                                        temp_location.startswith("'")
                                        and temp_location.endswith("'")
                                    ):
                                        install_location_cleaned = temp_location[1:-1]
                                app_details["InstallLocation"] = (
                                    install_location_cleaned
                                )
                                if install_location_cleaned and os.path.isdir(
                                    install_location_cleaned
                                ):
                                    app_details["PathStatus"] = "OK"
                                    if calculate_disk_usage_flag:
                                        try:
                                            dir_size = get_directory_size(
                                                install_location_cleaned,
                                                calculate_disk_usage_flag,
                                            )
                                            app_details["InstallLocationSize"] = (
                                                format_size(
                                                    dir_size, calculate_disk_usage_flag
                                                )
                                            )
                                        except DirectorySizeError as e_size:
                                            app_details["InstallLocationSize"] = (
                                                "N/A (Size Error)"
                                            )
                                            app_details["Remarks"] += (
                                                f"Size calc error: {e_size};"
                                            )
                                elif install_location_cleaned and os.path.isfile(
                                    install_location_cleaned
                                ):
                                    app_details["PathStatus"] = "OK (File)"
                                    app_details["Remarks"] += (
                                        " InstallLocation is a file;"
                                    )
                                    if calculate_disk_usage_flag:
                                        try:
                                            file_size = os.path.getsize(
                                                install_location_cleaned
                                            )
                                            app_details["InstallLocationSize"] = (
                                                format_size(
                                                    file_size, calculate_disk_usage_flag
                                                )
                                            )
                                        except OSError:
                                            app_details["InstallLocationSize"] = (
                                                "N/A (Access Error)"
                                            )
                                elif install_location_cleaned:
                                    app_details["PathStatus"] = "Path Not Found"
                                    app_details["Remarks"] += (
                                        " Broken install path (Actionable);"
                                    )
                                else:
                                    app_details["PathStatus"] = (
                                        "No Valid Path in Registry"
                                    )
                            except FileNotFoundError:
                                app_details["InstallLocation"] = "N/A"
                                app_details["PathStatus"] = "No Path in Registry"
                            except OSError as e:
                                app_details["InstallLocation"] = (
                                    f"Path Read Error: {e.strerror}"
                                )
                                app_details["PathStatus"] = "Error"
                            if app_details["DisplayName"] and not app_details[
                                "DisplayName"
                            ].startswith("{"):
                                software_list.append(app_details)
                    except OSError as e_val:
                        logging.warning(
                            f"OSError processing subkey {subkey_name} under {path_suffix}: {e_val}"
                        )
                    except Exception as e_inner:
                        logging.error(
                            f"Unexpected error processing subkey {subkey_name} under {path_suffix}: {e_inner}",
                            exc_info=True,
                        )
        except FileNotFoundError:
            logging.info(
                f"Registry path not found (this might be normal): {hive_display_name} - {path_suffix}"
            )
        except Exception as e_outer:
            logging.error(
                f"An error occurred accessing registry path {hive_display_name} - {path_suffix}: {e_outer}",
                exc_info=True,
            )
    return sorted(software_list, key=lambda x: str(x.get("DisplayName", "")).lower())


def output_to_json_combined(
    system_inventory_data,
    devenv_components_data,
    devenv_env_vars_data,
    devenv_issues_data,
    output_dir,
    filename="system_sage_combined_report.json",
):
    combined_data = {}
    is_sys_inv_placeholder = (
        system_inventory_data
        and len(system_inventory_data) == 1
        and system_inventory_data[0].get("Category") == "Informational"
    )
    if system_inventory_data and not is_sys_inv_placeholder:
        combined_data["systemInventory"] = system_inventory_data
    devenv_audit_data = {}
    if devenv_components_data:
        devenv_audit_data["detectedComponents"] = [
            comp.to_dict() for comp in devenv_components_data
        ]
    if devenv_env_vars_data:
        devenv_audit_data["environmentVariables"] = [
            ev.to_dict() for ev in devenv_env_vars_data
        ]
    if devenv_issues_data:
        devenv_audit_data["identifiedIssues"] = [
            issue.to_dict() for issue in devenv_issues_data
        ]
    if devenv_audit_data:
        combined_data["devEnvAudit"] = devenv_audit_data
    if not combined_data and is_sys_inv_placeholder:
        combined_data["systemInventory"] = system_inventory_data
    if not combined_data:
        logging.info("No data to save to JSON report.")
        return
    try:
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Combined JSON report successfully saved to {full_path}")
    except Exception as e:
        logging.error(
            f"Error saving combined JSON file to {output_dir}: {e}", exc_info=True
        )
        raise


def output_to_markdown_combined(
    system_inventory_data,
    devenv_components_data,
    devenv_env_vars_data,
    devenv_issues_data,
    output_dir,
    filename="system_sage_combined_report.md",
    include_system_sage_components_flag=True,
):
    try:
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(
                f"# System Sage Combined Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            f.write("## System Software Inventory\n\n")
            is_sys_inv_placeholder = (
                system_inventory_data
                and len(system_inventory_data) == 1
                and system_inventory_data[0].get("Category") == "Informational"
            )
            if system_inventory_data:
                if is_sys_inv_placeholder:
                    f.write(f"* {system_inventory_data[0].get('Remarks')}\\n\\n")
                else:
                    header = "| Application Name | Version | Publisher | Install Path | Size | Status | Remarks | Source Hive | Registry Key Path |\\n"
                    separator = "|---|---|---|---|---|---|---|---|---|\\n"
                    apps_data = [
                        app
                        for app in system_inventory_data
                        if app.get("Category") == "Application"
                    ]
                    comps_data = [
                        app
                        for app in system_inventory_data
                        if app.get("Category") == "Component/Driver"
                    ]
                    f.write("### Applications\\n")
                    if apps_data:
                        f.write(header)
                        f.write(separator)
                    for app_item in apps_data:  # Changed 'app' to 'app_item' to avoid conflict if 'app' is used later
                        f.write(
                            f"| {app_item.get('DisplayName', 'N/A')} | {app_item.get('DisplayVersion', 'N/A')} | {app_item.get('Publisher', 'N/A')} | {app_item.get('InstallLocation', 'N/A')} | {app_item.get('InstallLocationSize', 'N/A')} | {app_item.get('PathStatus', 'N/A')} | {app_item.get('Remarks', '')} | {app_item.get('SourceHive', 'N/A')} | {app_item.get('RegistryKeyPath', 'N/A')} |\\n"
                        )
                    else:
                        f.write("*No applications found.*\\n")
                        f.write("\\n")
                    if include_system_sage_components_flag:
                        f.write("### Components/Drivers\\n")
                        if comps_data:
                            f.write(header)
                            f.write(separator)
                        for comp_item in comps_data:  # Changed 'comp' to 'comp_item' for clarity and to ensure it's the loop variable
                            f.write(
                                f"| {comp_item.get('DisplayName', 'N/A')} | {comp_item.get('DisplayVersion', 'N/A')} | {comp_item.get('Publisher', 'N/A')} | {comp_item.get('InstallLocation', 'N/A')} | {comp_item.get('InstallLocationSize', 'N/A')} | {comp_item.get('PathStatus', 'N/A')} | {comp_item.get('Remarks', '')} | {comp_item.get('SourceHive', 'N/A')} | {comp_item.get('RegistryKeyPath', 'N/A')} |\\n"
                            )
                        else:
                            f.write(
                                "*No components/drivers found or component reporting is disabled.*\\n"
                            )
                            f.write("\\n")
            else:
                f.write("*No system inventory data collected.*\\n\\n")
            f.write("## Developer Environment Audit\\n\\n")
            if devenv_components_data or devenv_env_vars_data or devenv_issues_data:
                f.write("*DevEnvAudit details omitted for brevity in this example.*\n")
            else:
                f.write("*No data collected by Developer Environment Audit.*\n\n")
        logging.info(f"Combined Markdown report successfully saved to {full_path}")
    except Exception as e:
        logging.error(f"Error saving combined Markdown file: {e}", exc_info=True)
        raise


class SystemSageApp(customtkinter.CTk):
    def __init__(self, cli_args=None):
        super().__init__()
        self.cli_args = cli_args
        customtkinter.set_appearance_mode("System")

# --- Theme and Styling Constants ---
        self.corner_radius_std = 6
        self.corner_radius_soft = 8
        self.padding_std = 5
        self.padding_large = 10
        self.button_hover_color = ("gray70" )
        self.action_button_fg_color = "default"
        theme_path = resource_path("custom_theme.json")
        if os.path.exists(theme_path):
            customtkinter.set_default_color_theme(theme_path)
            logging.info(f"Successfully loaded custom theme from {theme_path}")
        else:
            customtkinter.set_default_color_theme("dark-blue")
            logging.info("Using default 'dark-blue' theme.")

        self.default_font = ("Roboto", 12)
        self.button_font = ("Roboto", 12, "bold")
        self.title_font = ("Roboto", 14, "bold") # Font for section titles
        self.option_add("*Font", self.default_font)
        self.title("System Sage V2.1 - Integrated OCL") # Version bump
        self.geometry("1200x850")

        self.inventory_scan_button = None
        self.devenv_audit_button = None
        self.inventory_table = None
        self.devenv_components_table = None
        self.devenv_env_vars_table = None
        self.devenv_issues_table = None
        self.ocl_profiles_table = None
        self.selected_ocl_profile_id = None
        self.status_bar = None
        self.scan_in_progress = False
        self.system_inventory_results = []
        self.devenv_components_results = []
        self.devenv_env_vars_results = []
        self.devenv_issues_results = []
        self.ocl_profile_details_text = None

        # --- MODIFIED: OCL button variables ---
        self.ocl_refresh_button = None
        self.ocl_new_bios_profile_button = None # Replaces ocl_save_new_button
        self.ocl_import_bios_profile_button = None # New button
        self.ocl_update_selected_button = None
        self.ocl_edit_profile_button = None

        self._setup_ui()
        if not IS_WINDOWS:
            self.after(100, self.start_system_inventory_scan)

    def _setup_ui(self):

        # Action Bar
        self.action_bar_frame = customtkinter.CTkFrame(self, corner_radius=0, height=50, border_width=0) # Corrected indentation
        self.action_bar_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(0, self.padding_std))

        action_button_height = 30
        action_button_padx = self.padding_std
        action_button_pady = (self.padding_std + 3, self.padding_std + 3)

        self.save_report_button = customtkinter.CTkButton(
            master=self.action_bar_frame,
            text="Save Report",
            command=self.save_combined_report,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            height=action_button_height,
            hover_color=self.button_hover_color,
        )
        self.save_report_button.pack(
            side=tk.LEFT, padx=action_button_padx, pady=action_button_pady
        )

        self.inventory_scan_button = customtkinter.CTkButton(
            master=self.action_bar_frame,
            text="System Inventory Scan",
            command=self.start_system_inventory_scan,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            height=action_button_height,
            hover_color=self.button_hover_color,
        )
        self.inventory_scan_button.pack(
            side=tk.LEFT, padx=action_button_padx, pady=action_button_pady
        )
        if not IS_WINDOWS:
            self.inventory_scan_button.configure(state=customtkinter.DISABLED)

        self.devenv_audit_button = customtkinter.CTkButton(
            master=self.action_bar_frame,
            text="DevEnv Audit",
            command=self.start_devenv_audit_scan,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            height=action_button_height,
            hover_color=self.button_hover_color,
        )
        self.devenv_audit_button.pack(
            side=tk.LEFT, padx=action_button_padx, pady=action_button_pady
        )

        self.exit_button = customtkinter.CTkButton(
            master=self.action_bar_frame,
            text="Exit",
            command=self.quit_app,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            height=action_button_height,
            hover_color=self.button_hover_color,
        )
        self.exit_button.pack(
            side=tk.RIGHT, padx=action_button_padx, pady=action_button_pady
        )

    def quit_app(self):
        """Closes the application."""
        self.destroy()

       # Main TabView
        self.main_notebook = customtkinter.CTkTabview(self, corner_radius=self.corner_radius_soft, border_width=0)
        self.main_notebook.pack(expand=True, fill="both", padx=self.padding_large, pady=(self.padding_std, self.padding_large))
        self.main_notebook.add("System Inventory")
        self.main_notebook.add("Developer Environment Audit")
        self.main_notebook.add("Overclocker's Logbook")
        # --- System Inventory Tab ---
        inventory_tab_frame = self.main_notebook.tab("System Inventory")
        inv_cols = [
            "Name",
            "Version",
            "Publisher",
            "Path",
            "Size",
            "Status",
            "Remarks",
            "SourceHive",
            "RegKey",
        ]
        self.inventory_table = CTkTable(
            master=inventory_tab_frame,
            column=len(inv_cols),
            values=[inv_cols],
            font=self.default_font,
            corner_radius=self.corner_radius_std,
            hover_color=self.button_hover_color,
        )
        self.inventory_table.pack(
            expand=True, fill="both", padx=self.padding_large, pady=self.padding_large
        )

        # --- Developer Environment Audit Tab ---
        devenv_tab_frame = self.main_notebook.tab("Developer Environment Audit")
        devenv_tab_frame.grid_columnconfigure(0, weight=1)

        outer_components_ctk_frame = customtkinter.CTkFrame(
            devenv_tab_frame, corner_radius=self.corner_radius_soft, border_width=1
        )
        outer_components_ctk_frame.grid(
            row=0,
            column=0,
            padx=self.padding_large,
            pady=(self.padding_large, self.padding_std),
            sticky="nsew",
        )
        outer_components_ctk_frame.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(
            master=outer_components_ctk_frame,
            text="Detected Components",
            font=self.title_font,
        ).pack(
            pady=(self.padding_std + 3, self.padding_std + 3), padx=self.padding_large
        )
        inner_components_ctk_frame = customtkinter.CTkFrame(
            outer_components_ctk_frame,
            corner_radius=self.corner_radius_std,
            border_width=0,
        )
        inner_components_ctk_frame.pack(
            fill="both",
            expand=True,
            padx=self.padding_large,
            pady=(0, self.padding_large),
        )
        # Original: comp_cols_list = ["ID", "Name", "Category", "Version", "Path", "Executable Path"]
        comp_cols_list = [
            "ID",
            "Name",
            "Category",
            "Version",
            "Path",
            "Executable Path",
            "Source",
            "DB Name",
        ]  # Updated
        self.devenv_components_table = CTkTable(
            master=inner_components_ctk_frame,
            column=len(comp_cols_list),
            values=[comp_cols_list],  # column count now reflects new headers
            font=self.default_font,
            corner_radius=self.corner_radius_std,
            hover_color=self.button_hover_color,
        )
        self.devenv_components_table.pack(
            expand=True, fill="both", padx=self.padding_std, pady=self.padding_std
        )

        outer_env_vars_ctk_frame = customtkinter.CTkFrame(
            devenv_tab_frame, corner_radius=self.corner_radius_soft, border_width=1
        )
        outer_env_vars_ctk_frame.grid(
            row=1,
            column=0,
            padx=self.padding_large,
            pady=self.padding_std,
            sticky="nsew",
        )
        outer_env_vars_ctk_frame.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(
            master=outer_env_vars_ctk_frame,
            text="Environment Variables",
            font=self.title_font,
        ).pack(
            pady=(self.padding_std + 3, self.padding_std + 3), padx=self.padding_large
        )
        inner_env_vars_ctk_frame = customtkinter.CTkFrame(
            outer_env_vars_ctk_frame,
            corner_radius=self.corner_radius_std,
            border_width=0,
        )
        inner_env_vars_ctk_frame.pack(
            fill="both",
            expand=True,
            padx=self.padding_large,
            pady=(0, self.padding_large),
        )
        env_cols_list = ["Name", "Value", "Scope"]
        self.devenv_env_vars_table = CTkTable(
            master=inner_env_vars_ctk_frame,
            column=len(env_cols_list),
            values=[env_cols_list],
            font=self.default_font,
            corner_radius=self.corner_radius_std,
            hover_color=self.button_hover_color,
        )
        self.devenv_env_vars_table.pack(
            expand=True, fill="both", padx=self.padding_std, pady=self.padding_std
        )

        outer_issues_ctk_frame = customtkinter.CTkFrame(
            devenv_tab_frame, corner_radius=self.corner_radius_soft, border_width=1
        )
        outer_issues_ctk_frame.grid(
            row=2,
            column=0,
            padx=self.padding_large,
            pady=self.padding_std,
            sticky="nsew",
        )
        outer_issues_ctk_frame.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(
            master=outer_issues_ctk_frame,
            text="Identified Issues",
            font=self.title_font,
        ).pack(
            pady=(self.padding_std + 3, self.padding_std + 3), padx=self.padding_large
        )
        inner_issues_ctk_frame = customtkinter.CTkFrame(
            outer_issues_ctk_frame, corner_radius=self.corner_radius_std, border_width=0
        )
        inner_issues_ctk_frame.pack(
            fill="both",
            expand=True,
            padx=self.padding_large,
            pady=(0, self.padding_large),
        )
        issue_cols_list = [
            "Severity",
            "Description",
            "Category",
            "Component ID",
            "Related Path",
        ]
        self.devenv_issues_table = CTkTable(
            master=inner_issues_ctk_frame,
            column=len(issue_cols_list),
            values=[issue_cols_list],
            font=self.default_font,
            corner_radius=self.corner_radius_std,
            hover_color=self.button_hover_color,
        )
        self.devenv_issues_table.pack(
            expand=True, fill="both", padx=self.padding_std, pady=self.padding_std
        )

        devenv_tab_frame.grid_rowconfigure(0, weight=1)
        devenv_tab_frame.grid_rowconfigure(1, weight=1)
        devenv_tab_frame.grid_rowconfigure(2, weight=1)

        # --- Overclocker's Logbook Tab ---
        ocl_tab_frame = self.main_notebook.tab("Overclocker's Logbook") # Corrected indentation
        ocl_tab_frame.grid_columnconfigure(0, weight=1)
        ocl_tab_frame.grid_rowconfigure(0, weight=2)
        ocl_tab_frame.grid_rowconfigure(1, weight=1)
        ocl_top_frame = customtkinter.CTkFrame(ocl_tab_frame, corner_radius=self.corner_radius_soft, border_width=1) # Corrected indentation
        ocl_top_frame.grid(row=0, column=0, padx=self.padding_large, pady=(self.padding_large, self.padding_std), sticky="nsew")
        ocl_top_frame.grid_columnconfigure(0, weight=1)
        ocl_top_frame.grid_rowconfigure(1, weight=1)
        customtkinter.CTkLabel(
            master=ocl_top_frame,
            text="Available Overclocking Profiles",
            font=self.title_font,
        ).grid(
            row=0,
            column=0,
            padx=self.padding_large,
            pady=(self.padding_std + 3, self.padding_std + 3),
        )
        inner_profiles_list_ctk_frame = customtkinter.CTkFrame(
            ocl_top_frame, corner_radius=self.corner_radius_std, border_width=0
        )
        inner_profiles_list_ctk_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=self.padding_large,
            pady=(0, self.padding_large),
        )
        initial_ocl_values = [["ID", "Profile Name", "Last Modified"]]
        self.ocl_profiles_table = CTkTable(
            master=inner_profiles_list_ctk_frame,
            column=3,
            values=initial_ocl_values,
            command=self.on_ocl_profile_select_ctktable, # This method is defined later, usually fine for linters
            font=self.default_font,
            corner_radius=self.corner_radius_std,
            hover_color=self.button_hover_color,
        )
        self.ocl_profiles_table.pack(
            expand=True, fill="both", padx=self.padding_std, pady=self.padding_std
        )

        ocl_bottom_frame = customtkinter.CTkFrame(ocl_tab_frame, corner_radius=self.corner_radius_soft, border_width=1) # Corrected indentation
        ocl_bottom_frame.grid(row=1, column=0, padx=self.padding_large, pady=(self.padding_std, self.padding_large), sticky="nsew")
        ocl_bottom_frame.grid_columnconfigure(0, weight=1)
        ocl_bottom_frame.grid_rowconfigure(0, weight=1)
        ocl_bottom_frame.grid_rowconfigure(1, weight=0)
        profile_details_outer_ctk_frame = customtkinter.CTkFrame(
            ocl_bottom_frame, fg_color="transparent", border_width=0
        )
        profile_details_outer_ctk_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=self.padding_large,
            pady=(0, self.padding_std),
        )
        profile_details_outer_ctk_frame.grid_columnconfigure(0, weight=1)
        profile_details_outer_ctk_frame.grid_rowconfigure(1, weight=1)

        customtkinter.CTkLabel(
            master=profile_details_outer_ctk_frame,
            text="Profile Details",
            font=self.title_font,
        ).grid(
            row=0, column=0, padx=0, pady=(self.padding_std + 3, self.padding_std + 3)
        )
        inner_profile_details_ctk_frame = customtkinter.CTkFrame(
            profile_details_outer_ctk_frame,
            corner_radius=self.corner_radius_std,
            border_width=0,
        )
        inner_profile_details_ctk_frame.grid(
            row=1, column=0, sticky="nsew", padx=0, pady=(0, self.padding_large)
        )
        self.ocl_profile_details_text = customtkinter.CTkTextbox(
            master=inner_profile_details_ctk_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=100,
            font=self.default_font,
            corner_radius=self.corner_radius_std,
            border_width=1,
        )
        self.ocl_profile_details_text.pack(
            expand=True, fill="both", padx=self.padding_std, pady=self.padding_std
        )

 # --- MODIFIED: OCL Action Buttons ---
        actions_ctk_frame = customtkinter.CTkFrame(ocl_bottom_frame, fg_color="transparent", border_width=0)
        actions_ctk_frame.grid(row=1, column=0, sticky="ew", padx=self.padding_large, pady=(self.padding_std, self.padding_large))

        self.ocl_refresh_button = customtkinter.CTkButton(master=actions_ctk_frame, text="Refresh List", command=self.refresh_ocl_profiles_list, font=self.button_font, corner_radius=self.corner_radius_soft)
        self.ocl_refresh_button.pack(side=tk.LEFT, padx=(0, self.padding_std), pady=self.padding_std)

        # --- NEW: "New BIOS Profile" Button ---
        self.ocl_new_bios_profile_button = customtkinter.CTkButton(master=actions_ctk_frame, text="New BIOS Profile...", command=self.create_new_bios_profile, font=self.button_font, corner_radius=self.corner_radius_soft)
        self.ocl_new_bios_profile_button.pack(side=tk.LEFT, padx=self.padding_std, pady=self.padding_std)

        # --- NEW: "Import BIOS Profile" Button ---
        self.ocl_import_bios_profile_button = customtkinter.CTkButton(master=actions_ctk_frame, text="Import BIOS Profile...", command=self.import_bios_profile, font=self.button_font, corner_radius=self.corner_radius_soft)
        self.ocl_import_bios_profile_button.pack(side=tk.LEFT, padx=self.padding_std, pady=self.padding_std)
        
        self.ocl_edit_profile_button = customtkinter.CTkButton(master=actions_ctk_frame, text="Edit Profile", command=self.edit_selected_ocl_profile, font=self.button_font, corner_radius=self.corner_radius_soft)
        self.ocl_edit_profile_button.pack(side=tk.LEFT, padx=self.padding_std, pady=self.padding_std)
        
        self.ocl_update_selected_button = customtkinter.CTkButton(master=actions_ctk_frame, text="Add Log Entry", command=self.update_selected_ocl_profile, font=self.button_font, corner_radius=self.corner_radius_soft)
        self.ocl_update_selected_button.pack(side=tk.LEFT, padx=self.padding_std, pady=self.padding_std)

        # Status Bar
        self.status_bar = customtkinter.CTkLabel(
            self, text="Ready", height=25, anchor="w", font=self.default_font
        )
        self.status_bar.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=self.padding_large,
            pady=(self.padding_std, self.padding_std),
        )

        # Load profiles on startup (AFTER status bar is created)
        self.refresh_ocl_profiles_list()

    def create_new_bios_profile(self):
        """Opens the OCL Profile Editor to create a new profile."""
        logging.info("Opening OCL Profile Editor in 'create' mode.")
        
        new_profile_obj = Profile(name="New BIOS Profile", description="A detailed BIOS profile.")
        
        editor = OclProfileEditor(master=self, mode='create', profile_obj=new_profile_obj, callback=self._save_profile_from_editor)
        # editor will be garbage collected if not assigned or kept alive, but CTkToplevel might manage its own lifecycle.

    def refresh_ocl_profiles_list(self):
        """Refreshes the list of OCL profiles in the GUI table."""
        if self.ocl_profiles_table is None:
            logging.warning("refresh_ocl_profiles_list: ocl_profiles_table is not initialized.")
            return

        # Clear existing rows except header
        for i in range(len(self.ocl_profiles_table.values) -1, 0, -1):
            self.ocl_profiles_table.delete_row(i)
        
        # If only header exists and it's not the default, reset it (optional, good for robustness)
        if len(self.ocl_profiles_table.values) == 0 or self.ocl_profiles_table.values[0] != ["ID", "Profile Name", "Last Modified"]:
            self.ocl_profiles_table.update_values([["ID", "Profile Name", "Last Modified"]])


        try:
            profiles = ocl_api.get_all_profiles()
            if profiles:
                for profile in profiles:
                    # Ensure last_modified is a string, format if it's a date object
                    last_modified_str = profile.get('last_modified', 'N/A')
                    if isinstance(last_modified_str, datetime.datetime):
                        last_modified_str = last_modified_str.strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.ocl_profiles_table.add_row([
                        str(profile.get('id', 'N/A')),
                        str(profile.get('name', 'N/A')),
                        last_modified_str
                    ])
                if self.status_bar: self.status_bar.configure(text=f"{len(profiles)} OCL profiles loaded.")
            else:
                # Add a placeholder row if no profiles are found
                self.ocl_profiles_table.add_row(["-", "No profiles found", "-"])
                if self.status_bar: self.status_bar.configure(text="No OCL profiles found in the database.")
            
            # After refreshing, clear selection and details view
            self.selected_ocl_profile_id = None
            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                self.ocl_profile_details_text.delete("0.0", tk.END)
                self.ocl_profile_details_text.insert("0.0", "Select a profile to view details.")
                self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)

        except Exception as e:
            logging.error(f"Error refreshing OCL profiles list: {e}", exc_info=True)
            if self.status_bar: self.status_bar.configure(text="Error loading OCL profiles.")
            # Optionally show a messagebox
            show_custom_messagebox(self, "OCL Error", f"Could not refresh profiles: {e}", "error")
            # Add a placeholder error row
            if len(self.ocl_profiles_table.values) <= 1: # if only header or empty
                 self.ocl_profiles_table.add_row(["-", "Error loading profiles", "-"])


    def inventory_scan_error(self, error_exception):
        """Handles errors that occur during the system inventory scan thread."""
        error_message = f"System Inventory scan failed: {error_exception}"
        logging.error(error_message, exc_info=True) # Log with stack trace
        if self.status_bar:
            self.status_bar.configure(text=error_message)
        
        # Ensure UI elements are reset to a usable state
        # self.finalize_scan_ui_state() # This will be called by the thread's finally block

        # Inform the user
        show_custom_messagebox(
            self, 
            "Scan Error", 
            f"An error occurred during the System Inventory scan: {error_exception}",
            dialog_type="error"
        )
        # Optionally, update the inventory display to show an error message
        if self.inventory_table:
            self.update_inventory_display([{"DisplayName": "Error during scan", "Remarks": str(error_exception), "Category": "Error"}])


    def import_bios_profile(self):
        """Imports a BIOS profile from a JSON file."""
        # Directly use the globally managed CTkFileDialog variable
        # It's either the real CTkFileDialog or the _BaseCTkFileDialogPlaceholder
        dialog = CTkFileDialog(title="Select BIOS Profile JSON File") # Removed master, filetypes
        filepath = dialog.path # Access .path directly

        if not filepath: # Placeholder's get() returns None, real one returns None on cancel
            logging.info("BIOS profile import cancelled or file dialog not available.")
            if isinstance(CTkFileDialog, _BaseCTkFileDialogPlaceholder): # Check if it was the placeholder
                 show_custom_messagebox(self, "File Dialog Info", "File selection was cancelled or the dialog is not fully functional.", "info")
            return

        try:
            profile_obj = load_from_json_file(filepath)
            if profile_obj:
                flat_settings = Profile.to_flat_list(profile_obj.settings)
                
                profile_id = ocl_api.create_new_profile(
                    name=profile_obj.name,
                    description=profile_obj.description,
                    initial_settings=flat_settings,
                    initial_logs=[f"Profile imported from {os.path.basename(filepath)}"]
                )
                if profile_id:
                    show_custom_messagebox(self, "Import Success", f"Successfully imported '{profile_obj.name}' into the database.", "info")
                    self.refresh_ocl_profiles_list()
                else:
                    show_custom_messagebox(self, "Import Error", "Failed to save the imported profile to the database.", "error")
            else:
                show_custom_messagebox(self, "Import Error", "Could not read or parse the selected JSON file.", "error")
        except Exception as e:
            logging.error(f"Error during BIOS profile import: {e}", exc_info=True)
            show_custom_messagebox(self, "Import Error", f"An unexpected error occurred: {e}", "error")

    def edit_selected_ocl_profile(self):
        """Opens the selected OCL profile in the new editor UI."""
        if self.selected_ocl_profile_id is None:
            show_custom_messagebox(self, "No Profile Selected", "Please select a profile to edit.", "warning")
            return

        logging.info(f"Opening OCL Profile Editor in 'edit' mode for ID: {self.selected_ocl_profile_id}")
        details = ocl_api.get_profile_details(self.selected_ocl_profile_id)

        if not details:
            show_custom_messagebox(self, "Error", f"Could not fetch details for profile ID: {self.selected_ocl_profile_id}.", "error")
            return

        profile_to_edit = Profile(
            name=str(details.get("name", "Default Name")), # Ensure string type
            description=str(details.get("description", "")), # Ensure string type
            profile_id=details.get("id")
        )
        flat_settings_from_db = details.get("settings", [])
        profile_to_edit.settings = Profile.from_flat_list(flat_settings_from_db)
        
        editor = OclProfileEditor(master=self, mode='edit', profile_obj=profile_to_edit, callback=self._save_profile_from_editor)

    def _save_profile_from_editor(self, profile_obj: Profile, mode: str): # Added mode parameter
        """Callback function for the OclProfileEditor to save data."""
        profile_id = None # Initialize profile_id to ensure it's bound
        # The profile_obj.settings are already hierarchical from the editor
        flat_settings = Profile.to_flat_list(profile_obj.settings)
        
        try:
            if mode == 'edit' and profile_obj.id is not None: # Use explicit mode
                # Update existing profile
                success = ocl_api.update_existing_profile(
                    profile_id=profile_obj.id,
                    name=profile_obj.name,
                    description=profile_obj.description,
                    settings_to_update=flat_settings # API expects flat list to replace all settings
                )
                if success:
                    show_custom_messagebox(self, "Success", f"Profile '{profile_obj.name}' updated successfully.", "info")
                else:
                    raise Exception("API returned failure on update.")
            elif mode == 'create': # Use explicit mode
                # Create new profile
                # Ensure profile_id is assigned the result of create_new_profile
                profile_id = ocl_api.create_new_profile(
                    name=profile_obj.name,
                    description=profile_obj.description,
                    initial_settings=flat_settings
                    # Consider if initial_logs should be added here for new profiles from editor
                )
                if profile_id:
                     show_custom_messagebox(self, "Success", f"New profile '{profile_obj.name}' created successfully with ID: {profile_id}.", "info")
                else:
                    raise Exception("API returned no ID on creation.")
            else:
                raise ValueError(f"Invalid mode '{mode}' received in _save_profile_from_editor.")
            
            self.refresh_ocl_profiles_list()
            # Optionally, try to reselect the profile if it was an edit
            if mode == 'edit' and profile_obj.id is not None:
                self.selected_ocl_profile_id = profile_obj.id
                self.after(100, self._reselect_ocl_profile_after_update) 
            elif mode == 'create' and profile_id: # If new profile was created and we got an ID
                self.selected_ocl_profile_id = profile_id
                self.after(100, self._reselect_ocl_profile_after_update)


        except Exception as e:
            logging.error(f"Failed to save profile from editor (mode: {mode}): {e}", exc_info=True)
            show_custom_messagebox(self, "Save Error", f"Could not save the profile to the database: {e}", "error")

    def _reselect_ocl_profile_after_update(self):
        """Refreshes the OCL profile details display area for the currently selected profile."""
        if self.selected_ocl_profile_id is None:
            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                self.ocl_profile_details_text.delete("0.0", tk.END)
                self.ocl_profile_details_text.insert("0.0", "Select a profile to view details.")
                self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)
            return

        details = ocl_api.get_profile_details(self.selected_ocl_profile_id)
        if self.ocl_profile_details_text:
            self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
            self.ocl_profile_details_text.delete("0.0", tk.END)
            if details:
                display_text = f"Profile: {details.get('name', 'N/A')} (ID: {details.get('id')})\\n"
                display_text += f"Description: {details.get('description', 'N/A')}\\n\\n"
                display_text += "Settings:\\n"
                if details.get("settings"):
                    for setting in details.get("settings", []):
                        display_text += f"  - {setting.get('category', 'N/A')} -> {setting.get('setting_name', 'N/A')}: {setting.get('setting_value', 'N/A')} (Type: {setting.get('value_type', 'str')})\\n"
                else:
                    display_text += "  (No settings for this profile)\\n"
                display_text += "\\nLogs:\\n"
                if details.get("logs"):
                    for log_entry in details.get("logs", []):
                        display_text += f"  - [{log_entry.get('timestamp', 'N/A')}]: {log_entry.get('log_text', 'N/A')}\\n"
                else:
                    display_text += "  (No logs for this profile)\\n"
                self.ocl_profile_details_text.insert("0.0", display_text)
            else:
                self.ocl_profile_details_text.insert("0.0", f"Could not retrieve details for profile ID: {self.selected_ocl_profile_id}. It may have been deleted.")
                self.selected_ocl_profile_id = None # Clear selection if invalid
            self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)

    def update_selected_ocl_profile(self):
        """Adds a new log entry to the selected OCL profile."""
        if self.selected_ocl_profile_id is None:
            show_custom_messagebox(self, "No Profile Selected", "Please select a profile to add a log to.", "warning")
            return

        dialog = customtkinter.CTkInputDialog(
            text="Enter log message:", 
            title="Add Log Entry"
        )
        # This method might need to be called on self (the root window) or a Toplevel if SystemSageApp is the root.
        # If CTkInputDialog needs a master, it would be 'self'. Assuming it works globally or self is implicit.
        log_text = dialog.get_input() 

        if log_text: # User entered something and didn't cancel
            try:
                success = ocl_api.add_log_to_profile(self.selected_ocl_profile_id, log_text)
                if success:
                    show_custom_messagebox(self, "Log Added", "Log entry added successfully.", "info")
                    self.refresh_ocl_profiles_list() # Refresh list (for Last Modified)
                    # Schedule the detail refresh after the list has had a chance to update
                    self.after(150, self._reselect_ocl_profile_after_update) 
                else:
                    show_custom_messagebox(self, "Error", "Failed to add log entry to the database.", "error")
            except Exception as e:
                logging.error(f"Error adding log entry: {e}", exc_info=True)
                show_custom_messagebox(self, "Error", f"An unexpected error occurred while adding log: {e}", "error")
        else:
            logging.info("Add log entry cancelled by user.")

    # --- DEPRECATED METHOD ---
    # We no longer need this complex, dialog-based method.
    def save_system_as_new_ocl_profile(self):
        show_custom_messagebox(self, "Action Changed", "This action has been replaced. Please use 'New BIOS Profile' to open the detailed editor or 'Import BIOS Profile' for JSON files.", "info")
        logging.warning("'save_system_as_new_ocl_profile' called, but is deprecated. User has been notified.")
        # All the old logic below this line in the original file should be removed.
        # The method should effectively end here.
        return


    def _update_action_buttons_state(self, state):
        button_state = (
            customtkinter.NORMAL if state == tk.NORMAL else customtkinter.DISABLED
        )
        if self.inventory_scan_button:
            if not IS_WINDOWS:
                self.inventory_scan_button.configure(state=customtkinter.DISABLED)
            else:
                self.inventory_scan_button.configure(state=button_state)
        if self.devenv_audit_button:
            self.devenv_audit_button.configure(state=button_state)

    def start_system_inventory_scan(self):
        if self.scan_in_progress and IS_WINDOWS:
            show_custom_messagebox(
                self,
                "Scan In Progress",
                "A scan is already running.",
                dialog_type="warning",
            )
            return
        if not IS_WINDOWS:
            if self.status_bar:
                self.status_bar.configure(
                    text="System Inventory (Registry Scan) is Windows-only."
                )
            placeholder_inventory = get_installed_software(False)
            self.update_inventory_display(placeholder_inventory)
            return
        else:  # IS_WINDOWS is True
            self.scan_in_progress = True
            if self.status_bar:
                self.status_bar.configure(text="Starting System Inventory Scan...")
            self._update_action_buttons_state(customtkinter.DISABLED)
            if self.inventory_table:
                self.inventory_table.delete_rows(
                    list(range(len(self.inventory_table.values)))
                )
            calc_disk = (
                self.cli_args.calculate_disk_usage
                if self.cli_args
                else DEFAULT_CALCULATE_DISK_USAGE
            )
            thread = Thread(
                target=self.run_system_inventory_thread, args=(calc_disk,), daemon=True
            )
            thread.start()

    def run_system_inventory_thread(self, calculate_disk_usage_flag):
        try:
            software_list = get_installed_software(calculate_disk_usage_flag)
            self.system_inventory_results = software_list # Store results
            self.after(0, self._update_inventory_display_from_thread, software_list)
            self.save_system_inventory_report(software_list)
        except Exception as e:
            logging.error(
                f"Error in system inventory thread: {e}\n{traceback.format_exc()}"
            )
            self.after(0, self._inventory_scan_error_from_thread, e)
        finally:
            self.after(0, self.finalize_scan_ui_state) # Centralized call

    def _update_inventory_display_from_thread(self, software_list):
        """Helper to call inventory display update from thread."""
        self.update_inventory_display(software_list)
        if self.status_bar:
            self.status_bar.configure(text="System Inventory Scan completed.")

    def _inventory_scan_error_from_thread(self, error_exception):
        """Helper to call inventory error handler from thread."""
        self.inventory_scan_error(error_exception)

    def save_system_inventory_report(self, software_list):
        output_dir = "output_data/system_inventory/"
        try:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"system_inventory_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            full_path = os.path.join(output_dir, filename)

              # Prepare data for JSON dump. software_list is a list of dictionaries.
            # We can wrap it for consistency or add metadata.
            report_data = {
                "report_generated_at": datetime.datetime.now().isoformat(),
                "system_inventory": software_list
            }
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=4)
            logging.info(f"System inventory report successfully saved to {full_path}")
        except Exception as e:
            logging.error(f"Error saving system inventory report: {e}")

    # --- DevEnv Audit Scan Methods ---
    def _clear_devenv_tables(self):
        """Clears the DevEnv audit tables and resets headers."""
        comp_cols_list = ["ID", "Name", "Category", "Version", "Path", "Executable Path", "Source", "DB Name"]
        env_cols_list = ["Name", "Value", "Scope"]
        issue_cols_list = ["Severity", "Description", "Category", "Component ID", "Related Path"]

        if self.devenv_components_table:
            self.devenv_components_table.update_values([comp_cols_list])
        if self.devenv_env_vars_table:
            self.devenv_env_vars_table.update_values([env_cols_list])
        if self.devenv_issues_table:
            self.devenv_issues_table.update_values([issue_cols_list])

    def start_devenv_audit_scan(self):
        if self.scan_in_progress:
            show_custom_messagebox(self, "Scan In Progress", "A scan is already running.", dialog_type="warning")
            return

        self.scan_in_progress = True
        if self.status_bar:
            self.status_bar.configure(text="Starting Developer Environment Audit...")
        self._update_action_buttons_state(customtkinter.DISABLED)
        self._clear_devenv_tables()

        # Clear previous results
        self.devenv_components_results = []
        self.devenv_env_vars_results = []
        self.devenv_issues_results = []

        thread = Thread(target=self.run_devenv_audit_thread, daemon=True)
        thread.start()

    def run_devenv_audit_thread(self): # Corrected indentation
        try:
            # EnvironmentScanner loads its own configuration internally
            scanner = EnvironmentScanner() 
            # Corrected method call to run_scan()
            components, env_vars, issues = scanner.run_scan() 
         
            # Store results
            self.devenv_components_results = components if components else []
            self.devenv_env_vars_results = env_vars if env_vars else []
            self.devenv_issues_results = issues if issues else []
            
            self.after(0, self._update_devenv_audit_display_from_thread, components, env_vars, issues)
        except Exception as e:
            logging.error(f"Error in DevEnv audit thread: {e}\\n{traceback.format_exc()}")
            self.after(0, self._devenv_audit_error_from_thread, e)
        finally:
            self.after(0, self.finalize_scan_ui_state)

    def _devenv_audit_error_from_thread(self, error_exception):
        """Helper to call devenv audit error handler from thread."""
        # Assuming self.devenv_audit_error method is defined to handle the error
        self.devenv_audit_error(error_exception)

    def _update_devenv_audit_display_from_thread(self, components, env_vars, issues):
        """Helper to call DevEnv display update from thread."""
        self.update_devenv_audit_display(components, env_vars, issues)
        if self.status_bar:
            self.status_bar.configure(text="Developer Environment Audit completed.")
        # self.finalize_scan_ui_state() # Called by the thread's finally block

    def update_devenv_audit_display(self, components, env_vars, issues):
        # Update Components Table
        if self.devenv_components_table:
            comp_cols_list = ["ID", "Name", "Category", "Version", "Path", "Executable Path", "Source", "DB Name"]
            comp_values = [comp_cols_list]
            if components:
                for comp in components:
                    c = comp.to_dict()
                    comp_values.append([
                        str(c.get("id", "N/A")), str(c.get("name", "N/A")), str(c.get("category", "N/A")),
                        str(c.get("version", "N/A")), str(c.get("path", "N/A")), str(c.get("executable_path", "N/A")),
                        str(c.get("source", "N/A")), str(c.get("db_name", "N/A"))
                    ])
            else:
                comp_values.append(["No components detected.", "", "", "", "", "", "", ""])
            self.devenv_components_table.update_values(comp_values)

        # Update Environment Variables Table
        if self.devenv_env_vars_table:
            env_cols_list = ["Name", "Value", "Scope"]
            env_values = [env_cols_list]
            if env_vars:
                for ev in env_vars:
                    e = ev.to_dict()
                    env_values.append([
                        str(e.get("name", "N/A")), str(e.get("value", "N/A")), str(e.get("scope", "N/A"))
                    ])
            else:
                env_values.append(["No environment variables detected.", "", ""])
            self.devenv_env_vars_table.update_values(env_values)

        # Update Identified Issues Table
        if self.devenv_issues_table:
            issue_cols_list = ["Severity", "Description", "Category", "Component ID", "Related Path"]
            issue_values = [issue_cols_list]
            if issues:
                for issue in issues:
                    i = issue.to_dict()
                    issue_values.append([
                        str(i.get("severity", "N/A")), str(i.get("description", "N/A")), str(i.get("category", "N/A")),
                        str(i.get("component_id", "N/A")), str(i.get("related_path", "N/A"))
                    ])
            else:
                issue_values.append(["No issues identified.", "", "", "", ""])
            self.devenv_issues_table.update_values(issue_values)

    def devenv_audit_error(self, error_exception):
        error_message = f"DevEnv Audit scan failed: {error_exception}"
        logging.error(error_message, exc_info=True)
        if self.status_bar:
            self.status_bar.configure(text=error_message)
        
        show_custom_messagebox(
            self, 
            "DevEnv Audit Error", 
            f"An error occurred during the Developer Environment Audit: {error_exception}",
            dialog_type="error"
        )
        # Optionally, update the devenv tables to show an error message
        self._clear_devenv_tables() # Clear tables first
        if self.devenv_components_table:
             self.devenv_components_table.add_row([f"Error: {error_exception}", "", "", "", "", "", "", ""])


    def finalize_scan_ui_state(self):
        self.scan_in_progress = False
        self._update_action_buttons_state(customtkinter.NORMAL)

    def update_inventory_display(self, software_list):
        if self.inventory_table:
            header = [
                "Name",
                "Version",
                "Publisher",
                "Path",
                "Size",
                "Status",
                "Remarks",
                "SourceHive",
                "RegKey",
            ]
            table_values = [header]  # Start with the header

            if not software_list:
                # If the list is completely empty, add a placeholder that respects columns
                placeholder = ["No software found.", "", "", "", "", "", "", "", ""]
                table_values.append(placeholder)
            elif (
                len(software_list) == 1
                and software_list[0].get("Category") == "Informational"
            ):
                # Handle the specific non-Windows placeholder message
                placeholder = [
                    software_list[0].get("Remarks", "N/A"),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
                table_values.append(placeholder)
            else:
                # Populate with actual software data
                for app in software_list:
                    table_values.append(
                        [
                            str(app.get("DisplayName", "N/A")),
                            str(app.get("DisplayVersion", "N/A")),
                            str(app.get("Publisher", "N/A")),
                            str(app.get("InstallLocation", "N/A")),
                            str(app.get("InstallLocationSize", "N/A")),
                            str(app.get("PathStatus", "N/A")),
                            str(app.get("Remarks", "")),
                            str(app.get("SourceHive", "N/A")),
                            str(app.get("RegistryKeyPath", "N/A")),
                        ]
                    )

            self.inventory_table.update_values(table_values)
    def on_ocl_profile_select_ctktable(self, selection_data):
        selected_data_row_index = selection_data.get("row")
        if selected_data_row_index is None:
            logging.debug("on_ocl_profile_select_ctktable: No row index in selection_data.")
            return

        profile_id_val_str = None
        selected_row_values = None
        
        # The CTkTable returns the index of the clicked row in the currently displayed data.
        # If the table has a header row at index 0 of its internal 'values' list, 
        # and the user clicks the first data row, 'selected_data_row_index' will be 0.
        # The actual data in `self.ocl_profiles_table.values` would be at `selected_data_row_index + 1`
        # if `self.ocl_profiles_table.values[0]` is the header.
        # However, CTkTable's `command` usually gives the index relative to data rows if header is configured.
        # Let's assume `selected_data_row_index` is the 0-based index of the *data* row clicked.
        # So, if `self.ocl_profiles_table.values[0]` is header, data starts at `self.ocl_profiles_table.values[selected_data_row_index + 1]`.
        data_list_index = selected_data_row_index + 1 # Index in the .values list, assuming header is values[0]

        if self.ocl_profiles_table is None or not hasattr(self.ocl_profiles_table, "values"):
            logging.warning("on_ocl_profile_select_ctktable: ocl_profiles_table is not initialized or has no values.")
            return

        if not (1 <= data_list_index < len(self.ocl_profiles_table.values)): 
            logging.warning(f"on_ocl_profile_select_ctktable: Selection index {selected_data_row_index} (data list index {data_list_index}) is out of bounds for table with {len(self.ocl_profiles_table.values)} total rows (incl. header).")
            # This can happen if the table is empty or only has a header and it's clicked.
            self.selected_ocl_profile_id = None
            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                self.ocl_profile_details_text.delete("0.0", tk.END)
                self.ocl_profile_details_text.insert("0.0", "No profile selected or table is empty.")
                self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)
            return
        
        try:
            selected_row_values = self.ocl_profiles_table.values[data_list_index]
            profile_id_val_str = selected_row_values[0] 

            if not str(profile_id_val_str).isdigit():
                logging.info(f"on_ocl_profile_select_ctktable: Non-data row clicked or invalid ID. Content: '{profile_id_val_str}'")
                self.selected_ocl_profile_id = None
                if self.ocl_profile_details_text:
                    self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                    self.ocl_profile_details_text.delete("0.0", tk.END)
                    self.ocl_profile_details_text.insert("0.0", "Select a valid profile to view details.")
                    self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)
                return

            self.selected_ocl_profile_id = int(profile_id_val_str)
            logging.info(f"OCL profile selected. ID: {self.selected_ocl_profile_id}")
            details = ocl_api.get_profile_details(self.selected_ocl_profile_id)

            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                self.ocl_profile_details_text.delete("0.0", tk.END)
                if details:
                    hierarchical_settings = Profile.from_flat_list(details.get("settings", []))

                    display_text = f"Profile: {details.get('name', 'N/A')} (ID: {details.get('id')})\\n"
                    display_text += f"Description: {details.get('description', 'N/A')}\\n\\n"

                    display_text += "Settings:\\n"
                    if hierarchical_settings:
                        for category, cat_settings_list in hierarchical_settings.items():
                            display_text += f"  Category: {category}\\n"
                            if cat_settings_list:
                                for setting_entry in cat_settings_list: # Renamed to setting_entry
                                    if isinstance(setting_entry, dict):
                                        setting_name = setting_entry.get('setting_name', 'N/A')
                                        setting_value = setting_entry.get('setting_value', 'N/A')
                                        value_type = setting_entry.get('value_type', 'str')
                                        display_text += f"    - {setting_name}: {setting_value} (Type: {value_type})\\n"
                                    elif isinstance(setting_entry, str):
                                        display_text += f"    - {setting_entry}\\n"
                                    else: # Attempt to treat as an object (e.g., BIOSSetting instance)
                                        try:
                                            setting_name = getattr(setting_entry, 'setting_name', 'N/A')
                                            setting_value = getattr(setting_entry, 'setting_value', 'N/A')
                                            value_type = getattr(setting_entry, 'value_type', 'str')
                                            display_text += f"    - {setting_name}: {setting_value} (Type: {value_type})\\n"
                                        except AttributeError:
                                            display_text += f"    - Unknown setting format: {str(setting_entry)}\\n"
                            else:
                                display_text += "             (No settings in this category)\\n"
                    else:
                        display_text += "  (No settings defined for this profile)\\n"

                    display_text += "\\nLogs:\\n"
                    if details.get("logs"):
                        for log_entry in details.get("logs", []): # Ensure 'log_entry' is used
                            display_text += f"  - [{log_entry.get('timestamp', 'N/A')}]: {log_entry.get('log_text', 'N/A')}\\n"
                    else:
                        display_text += "  (No logs for this profile)\\n"

                    self.ocl_profile_details_text.insert("0.0", display_text)
                else:
                    self.ocl_profile_details_text.insert("0.0", f"No details found for profile ID: {self.selected_ocl_profile_id}")
                    self.selected_ocl_profile_id = None # Clear selection if details not found
                self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)
        except ValueError:
            logging.error(f"Error converting profile ID '{profile_id_val_str}' to int.", exc_info=True)
            show_custom_messagebox(self, "OCL Error", f"Could not process profile ID: '{profile_id_val_str}'.", dialog_type="error")
            self.selected_ocl_profile_id = None
        except IndexError:
            logging.error(f"Error accessing profile data at index {data_list_index}. Row content: {selected_row_values if selected_row_values else 'Unknown'}", exc_info=True)
            show_custom_messagebox(self, "OCL Error", "Could not retrieve all data for the selected profile row.", dialog_type="error")
            self.selected_ocl_profile_id = None
        except Exception as e:
            logging.error(f"Unexpected error processing OCL profile selection: {e}", exc_info=True)
            show_custom_messagebox(self, "OCL Error", f"An unexpected error occurred: {e}", dialog_type="error")
            self.selected_ocl_profile_id = None

    def save_combined_report(self):
        # Directly use the globally managed CTkFileDialog variable
        dialog = CTkFileDialog(
            title="Select Output Directory", open_folder=True
        ) # Removed master
        output_dir = dialog.path # Access .path directly

        if not output_dir: # Placeholder's get() returns None, real one returns None on cancel
            logging.info("Save report cancelled or file dialog not available.")
            # Optionally, inform if it was the placeholder, though it logs itself.
            if isinstance(CTkFileDialog, _BaseCTkFileDialogPlaceholder):
                 show_custom_messagebox(self, "File Dialog Info", "Directory selection was cancelled or the dialog is not fully functional.", "info")
            return
        try:
            md_include_components = (
                self.cli_args.markdown_include_components_flag
                if self.cli_args
                else DEFAULT_MARKDOWN_INCLUDE_COMPONENTS
            )
            sys_inv_data_for_report = self.system_inventory_results
            is_sys_inv_placeholder = (
                self.system_inventory_results
                and len(self.system_inventory_results) == 1
                and self.system_inventory_results[0].get("Category") == "Informational"
            )

            if is_sys_inv_placeholder and (
                self.devenv_components_results
                or self.devenv_env_vars_results
                or self.devenv_issues_results
            ):
                sys_inv_data_for_report = [] # Do not include placeholder if other data exists
            
            # Ensure devenv results are handled correctly if they are None or empty
            devenv_components = self.devenv_components_results if self.devenv_components_results else []
            devenv_env_vars = self.devenv_env_vars_results if self.devenv_env_vars_results else []
            devenv_issues = self.devenv_issues_results if self.devenv_issues_results else []

            output_to_json_combined(
                sys_inv_data_for_report,
                devenv_components, # Pass potentially empty lists
                devenv_env_vars,
                devenv_issues,
                output_dir,
            )
            output_to_markdown_combined(
                sys_inv_data_for_report,
                devenv_components,
                devenv_env_vars,
                devenv_issues,
                output_dir,
                include_system_sage_components_flag=md_include_components,
            )
            show_custom_messagebox(
                self,
                "Reports Saved",
                f"Combined reports saved to: {output_dir}",
                dialog_type="info",
            )
        except Exception as e:
            logging.error(
                f"Error saving reports: {e}\\n{traceback.format_exc()}", exc_info=True # Ensure full traceback is logged
            )
            show_custom_messagebox(
                self, "Save Error", f"Failed to save reports: {e}", dialog_type="error"
            )