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
# --- UI Imports ---
import customtkinter
from tkinter import ttk
# CTkFileDialog will be imported in the fallback logic below
from tkinter import messagebox # Import messagebox explicitly
from typing import Optional

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
    # Use hasattr to avoid AttributeError if _MEIPASS is not present
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS  # type: ignore
    else:
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
                            except (FileNotFoundError, OSError):
                                app_details["DisplayName"] = subkey_name
                            entry_id_name = app_details["DisplayName"]
                            entry_id_version = "N/A"
                            try:
                                app_details["DisplayVersion"] = str(
                                    winreg.QueryValueEx(app_key, "DisplayVersion")[0]
                                )
                                entry_id_version = app_details["DisplayVersion"]  # type: ignore
                            except (FileNotFoundError, OSError):
                                app_details["DisplayVersion"] = "N/A"
                            entry_id = (entry_id_name, entry_id_version)
                            if entry_id in processed_entries:
                                continue
                            processed_entries.add(entry_id)
                            try:
                                app_details["Publisher"] = str(
                                    winreg.QueryValueEx(app_key, "Publisher")[0]
                                )  # type: ignore
                            except (FileNotFoundError, OSError):
                                app_details["Publisher"] = "N/A"
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
                            except (FileNotFoundError, OSError):
                                app_details["InstallLocation"] = "N/A"
                                app_details["PathStatus"] = "No Path in Registry"
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
        self.button_hover_color = ("gray70", "gray30")
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
        self.title_font = ("Roboto", 14, "bold")
        self.option_add("*Font", self.default_font)

        # --- Initialize Instance Attributes ---
        self.inventory_scan_button: Optional[customtkinter.CTkButton] = None
        self.devenv_audit_button: Optional[customtkinter.CTkButton] = None
        self.inventory_tree: Optional[ttk.Treeview] = None
        self.devenv_components_tree: Optional[ttk.Treeview] = None
        self.devenv_env_vars_tree: Optional[ttk.Treeview] = None
        self.devenv_issues_tree: Optional[ttk.Treeview] = None
        self.ocl_profiles_tree: Optional[ttk.Treeview] = None
        self.selected_ocl_profile_id: Optional[int] = None
        self.status_bar: Optional[customtkinter.CTkLabel] = None
        self.scan_in_progress = False
        self.system_inventory_results: list = []
        self.devenv_components_results: list = []
        self.devenv_env_vars_results: list = []
        self.devenv_issues_results: list = []
        self.ocl_profile_details_text: Optional[customtkinter.CTkTextbox] = None
        self.ocl_edit_profile_button: Optional[customtkinter.CTkButton] = None
        self.ocl_export_profile_button: Optional[customtkinter.CTkButton] = None
        self.ocl_delete_profile_button: Optional[customtkinter.CTkButton] = None

        # --- Main Application Window Setup ---
        self.title("System Sage - Comprehensive System Analysis")
        self.geometry("1400x900")

        # --- Create Main Layout Frames ---
        self.action_bar_frame = customtkinter.CTkFrame(self, corner_radius=0, height=50, border_width=0)
        self.action_bar_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(0, self.padding_std))

        self.main_notebook = customtkinter.CTkTabview(self, corner_radius=self.corner_radius_soft, border_width=0)
        self.main_notebook.pack(expand=True, fill="both", padx=self.padding_large, pady=(self.padding_std, self.padding_large))

        # --- Populate UI ---
        self._setup_ui()

        # --- Perform Initial Actions ---
        self.after(100, self.perform_initial_scans)

    def _setup_ui(self):
        """Create and configure all UI elements within the main layout frames."""

        # --- Action Bar Buttons ---
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
        self.save_report_button.pack(side=tk.LEFT, padx=action_button_padx, pady=action_button_pady)

        self.inventory_scan_button = customtkinter.CTkButton(
            master=self.action_bar_frame,
            text="System Inventory Scan",
            command=self.start_system_inventory_scan,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            height=action_button_height,
            hover_color=self.button_hover_color,
        )
        self.inventory_scan_button.pack(side=tk.LEFT, padx=action_button_padx, pady=action_button_pady)
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
        self.devenv_audit_button.pack(side=tk.LEFT, padx=action_button_padx, pady=action_button_pady)

        self.exit_button = customtkinter.CTkButton(
            master=self.action_bar_frame,
            text="Exit",
            command=self.quit_app,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            height=action_button_height,
            hover_color=self.button_hover_color,
        )
        self.exit_button.pack(side=tk.RIGHT, padx=action_button_padx, pady=action_button_pady)

        # --- Main TabView Setup ---
        self.main_notebook.add("System Inventory")
        self.main_notebook.add("Developer Environment Audit")
        self.main_notebook.add("Overclocker's Logbook")

        # --- System Inventory Tab (ttk.Treeview version) ---
        inventory_tab_frame = self.main_notebook.tab("System Inventory")
        inventory_tab_frame.grid_rowconfigure(0, weight=1)
        inventory_tab_frame.grid_columnconfigure(0, weight=1)
        inventory_outer_frame = customtkinter.CTkFrame(inventory_tab_frame, corner_radius=0, fg_color="transparent")
        inventory_outer_frame.grid(row=0, column=0, sticky="nsew", padx=self.padding_std, pady=self.padding_std)
        inventory_outer_frame.grid_rowconfigure(1, weight=1)
        inventory_outer_frame.grid_columnconfigure(0, weight=1)

        # Filter entry
        filter_frame = customtkinter.CTkFrame(inventory_outer_frame, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        filter_label = customtkinter.CTkLabel(filter_frame, text="Filter:")
        filter_label.pack(side="left", padx=(0, 6))
        self.inventory_filter_var = tk.StringVar()
        filter_entry = customtkinter.CTkEntry(filter_frame, textvariable=self.inventory_filter_var, width=220)
        filter_entry.pack(side="left", fill="x", expand=True)
        filter_entry.bind("<KeyRelease>", lambda e: self.update_inventory_display())

        # Treeview setup
        inv_cols = ["Name", "Version", "Publisher", "Path", "Size", "Status", "Remarks", "SourceHive", "RegKey"]
        self.inventory_tree = ttk.Treeview(inventory_outer_frame, columns=inv_cols, show="headings", selectmode="browse")
        for col in inv_cols:
            self.inventory_tree.heading(col, text=col, command=lambda c=col: self._sort_inventory_by_column(c, False))
            self.inventory_tree.column(col, width=120, anchor="w", stretch=True)
        self.inventory_tree.grid(row=1, column=0, sticky="nsew")

        # Add vertical scrollbar
        vsb = ttk.Scrollbar(inventory_outer_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

        # Add horizontal scrollbar
        hsb = ttk.Scrollbar(inventory_outer_frame, orient="horizontal", command=self.inventory_tree.xview)
        self.inventory_tree.configure(xscrollcommand=hsb.set)
        hsb.grid(row=2, column=0, sticky="ew")

        # Style Treeview to match customtkinter as much as possible
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#23272e",
                        foreground="#e0e0e0",
                        rowheight=28,
                        fieldbackground="#23272e",
                        font=("Segoe UI", 11))
        style.configure("Treeview.Heading",
                        background="#1a1d22",
                        foreground="#aeea00",
                        font=("Segoe UI", 11, "bold"))
        style.map("Treeview.Heading",
                  background=[("active", "#263238")])

        self.inventory_tree.bind("<ButtonRelease-1>", self._clear_inventory_sort_state)
        self._inventory_sort_column = None
        self._inventory_sort_reverse = False

        # --- Developer Environment Audit Tab ---
        devenv_audit_tab_frame = self.main_notebook.tab("Developer Environment Audit")
        devenv_audit_tab_frame.grid_rowconfigure(0, weight=1)
        devenv_audit_tab_frame.grid_columnconfigure(0, weight=1)

        devenv_notebook = customtkinter.CTkTabview(devenv_audit_tab_frame, corner_radius=self.corner_radius_soft)
        devenv_notebook.pack(expand=True, fill="both", padx=self.padding_std, pady=self.padding_std)
        devenv_notebook.add("Detected Components")
        devenv_notebook.add("Environment Variables")
        devenv_notebook.add("Issues Found")

        # DevEnv Components (ttk.Treeview)
        devenv_components_tab = devenv_notebook.tab("Detected Components")
        devenv_components_tab.grid_rowconfigure(0, weight=1)
        devenv_components_tab.grid_columnconfigure(0, weight=1)
        comp_cols = ["ID", "Name", "Category", "Version", "Path", "Executable Path", "Source", "DB Name"]
        self.devenv_components_tree = ttk.Treeview(devenv_components_tab, columns=comp_cols, show="headings", selectmode="browse")
        for col in comp_cols:
            self.devenv_components_tree.heading(col, text=col, command=lambda c=col: self._sort_treeview_by_column(self.devenv_components_tree, c, False))
            self.devenv_components_tree.column(col, width=120, anchor="w", stretch=True)
        self.devenv_components_tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(devenv_components_tab, orient="vertical", command=self.devenv_components_tree.yview)
        self.devenv_components_tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(devenv_components_tab, orient="horizontal", command=self.devenv_components_tree.xview)
        self.devenv_components_tree.configure(xscrollcommand=hsb.set)
        hsb.grid(row=1, column=0, sticky="ew")

        # DevEnv Env Vars (ttk.Treeview)
        devenv_env_vars_tab = devenv_notebook.tab("Environment Variables")
        devenv_env_vars_tab.grid_rowconfigure(0, weight=1)
        devenv_env_vars_tab.grid_columnconfigure(0, weight=1)
        env_cols = ["Name", "Value", "Scope"]
        self.devenv_env_vars_tree = ttk.Treeview(devenv_env_vars_tab, columns=env_cols, show="headings", selectmode="browse")
        for col in env_cols:
            self.devenv_env_vars_tree.heading(col, text=col, command=lambda c=col: self._sort_treeview_by_column(self.devenv_env_vars_tree, c, False))
            self.devenv_env_vars_tree.column(col, width=120, anchor="w", stretch=True)
        self.devenv_env_vars_tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(devenv_env_vars_tab, orient="vertical", command=self.devenv_env_vars_tree.yview)
        self.devenv_env_vars_tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(devenv_env_vars_tab, orient="horizontal", command=self.devenv_env_vars_tree.xview)
        self.devenv_env_vars_tree.configure(xscrollcommand=hsb.set)
        hsb.grid(row=1, column=0, sticky="ew")

        # DevEnv Issues (ttk.Treeview)
        devenv_issues_tab = devenv_notebook.tab("Issues Found")
        devenv_issues_tab.grid_rowconfigure(0, weight=1)
        devenv_issues_tab.grid_columnconfigure(0, weight=1)
        issue_cols = ["Severity", "Description", "Category", "Component ID", "Related Path"]
        self.devenv_issues_tree = ttk.Treeview(devenv_issues_tab, columns=issue_cols, show="headings", selectmode="browse")
        for col in issue_cols:
            self.devenv_issues_tree.heading(col, text=col, command=lambda c=col: self._sort_treeview_by_column(self.devenv_issues_tree, c, False))
            self.devenv_issues_tree.column(col, width=120, anchor="w", stretch=True)
        self.devenv_issues_tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(devenv_issues_tab, orient="vertical", command=self.devenv_issues_tree.yview)
        self.devenv_issues_tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(devenv_issues_tab, orient="horizontal", command=self.devenv_issues_tree.xview)
        self.devenv_issues_tree.configure(xscrollcommand=hsb.set)
        hsb.grid(row=1, column=0, sticky="ew")

        # --- Overclocker's Logbook Tab ---
        ocl_tab_frame = self.main_notebook.tab("Overclocker's Logbook")
        ocl_tab_frame.grid_rowconfigure(0, weight=1) # List
        ocl_tab_frame.grid_rowconfigure(1, weight=1) # Details/Actions
        ocl_tab_frame.grid_columnconfigure(0, weight=1)

        # OCL Top Frame (Profile List, ttk.Treeview)
        ocl_top_frame = customtkinter.CTkFrame(ocl_tab_frame, corner_radius=self.corner_radius_soft, border_width=1)
        ocl_top_frame.grid(row=0, column=0, padx=self.padding_large, pady=self.padding_large, sticky="nsew")
        ocl_top_frame.grid_rowconfigure(1, weight=1)
        ocl_top_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(ocl_top_frame, text="Available BIOS Profiles", font=self.title_font).grid(row=0, column=0, padx=self.padding_large, pady=self.padding_std, sticky="w")

        ocl_cols = ["ID", "Profile Name", "Last Modified"]
        self.ocl_profiles_tree = ttk.Treeview(ocl_top_frame, columns=ocl_cols, show="headings", selectmode="browse")
        for col in ocl_cols:
            self.ocl_profiles_tree.heading(col, text=col, command=lambda c=col: self._sort_treeview_by_column(self.ocl_profiles_tree, c, False))
            self.ocl_profiles_tree.column(col, width=120, anchor="w", stretch=True)
        self.ocl_profiles_tree.grid(row=1, column=0, sticky="nsew", padx=self.padding_std, pady=self.padding_std)
        vsb = ttk.Scrollbar(ocl_top_frame, orient="vertical", command=self.ocl_profiles_tree.yview)
        self.ocl_profiles_tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")
        hsb = ttk.Scrollbar(ocl_top_frame, orient="horizontal", command=self.ocl_profiles_tree.xview)
        self.ocl_profiles_tree.configure(xscrollcommand=hsb.set)
        hsb.grid(row=2, column=0, sticky="ew")
        self.ocl_profiles_tree.bind("<<TreeviewSelect>>", self.on_ocl_profile_select)

        # OCL Bottom Frame (Details & Actions)
        ocl_bottom_frame = customtkinter.CTkFrame(ocl_tab_frame, corner_radius=self.corner_radius_soft, border_width=1)
        ocl_bottom_frame.grid(row=1, column=0, padx=self.padding_large, pady=(self.padding_std, self.padding_large), sticky="nsew")
        ocl_bottom_frame.grid_columnconfigure(0, weight=3)
        ocl_bottom_frame.grid_columnconfigure(1, weight=1)
        ocl_bottom_frame.grid_rowconfigure(0, weight=1)

        # Details View
        details_frame = customtkinter.CTkFrame(ocl_bottom_frame, corner_radius=self.corner_radius_std)
        details_frame.grid(row=0, column=0, sticky="nsew", padx=(self.padding_large, self.padding_std), pady=self.padding_large)
        details_frame.grid_rowconfigure(1, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(details_frame, text="Selected Profile Details", font=self.title_font).grid(row=0, column=0, padx=self.padding_large, pady=self.padding_std, sticky="w")
        self.ocl_profile_details_text = customtkinter.CTkTextbox(details_frame, wrap="word", state="disabled", font=self.default_font)
        self.ocl_profile_details_text.grid(row=1, column=0, sticky="nsew", padx=self.padding_large, pady=(0, self.padding_large))

        # Actions Panel
        actions_panel = customtkinter.CTkFrame(ocl_bottom_frame, corner_radius=self.corner_radius_std)
        actions_panel.grid(row=0, column=1, sticky="nsew", padx=(self.padding_std, self.padding_large), pady=self.padding_large)
        actions_panel.grid_columnconfigure(0, weight=1)

        action_button_config = {
            "font": self.button_font,
            "corner_radius": self.corner_radius_soft,
            "hover_color": self.button_hover_color,
        }

        self.ocl_refresh_button = customtkinter.CTkButton(actions_panel, text="Refresh List", command=self.refresh_ocl_profiles_list, **action_button_config)
        self.ocl_refresh_button.grid(row=0, column=0, sticky="ew", padx=self.padding_large, pady=self.padding_std)

        self.ocl_new_bios_profile_button = customtkinter.CTkButton(actions_panel, text="New BIOS Profile", command=self.create_new_bios_profile, **action_button_config)
        self.ocl_new_bios_profile_button.grid(row=1, column=0, sticky="ew", padx=self.padding_large, pady=self.padding_std)

        self.ocl_import_bios_profile_button = customtkinter.CTkButton(actions_panel, text="Import from File", command=self.import_bios_profile, **action_button_config)
        self.ocl_import_bios_profile_button.grid(row=2, column=0, sticky="ew", padx=self.padding_large, pady=self.padding_std)

        self.ocl_export_profile_button = customtkinter.CTkButton(actions_panel, text="Export Selected to File", command=self.export_selected_profile, state="disabled", **action_button_config)
        self.ocl_export_profile_button.grid(row=3, column=0, sticky="ew", padx=self.padding_large, pady=self.padding_std)
        
        self.ocl_edit_profile_button = customtkinter.CTkButton(actions_panel, text="Edit Selected Profile", command=self.edit_selected_profile, state="disabled", **action_button_config)
        self.ocl_edit_profile_button.grid(row=4, column=0, sticky="ew", padx=self.padding_large, pady=self.padding_std)

        # Special config for delete button to override hover color
        delete_button_config = action_button_config.copy()
        del delete_button_config['hover_color']

        self.ocl_delete_profile_button = customtkinter.CTkButton(actions_panel, text="Delete Selected", command=self.delete_selected_profile, state="disabled", fg_color="#D32F2F", hover_color="#B71C1C", **delete_button_config)
        self.ocl_delete_profile_button.grid(row=5, column=0, sticky="ew", padx=self.padding_large, pady=(self.padding_std, self.padding_large))

        # --- Status Bar ---
        self.status_bar = customtkinter.CTkLabel(self, text="Ready", anchor="w", padx=self.padding_large)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(self.padding_std, 0))


    def _prompt_devenv_audit_after_inventory(self):

        # Show a modal dialog: "Initial scan complete, scan devenvaudit now?" Yes/No
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Continue?")
        dialog.geometry("350x150")
        label = customtkinter.CTkLabel(dialog, text="Initial scan complete. Scan Developer Environment Audit now?", wraplength=320)
        label.pack(padx=20, pady=(30,10))
        def on_yes():
            dialog.destroy()
            self.start_devenv_audit_scan()
        def on_no():
            dialog.destroy()
            self.update_status_bar("DevEnvAudit scan skipped.", clear_after_ms=4000)
        btn_frame = customtkinter.CTkFrame(dialog)
        btn_frame.pack(pady=10)
        yes_btn = customtkinter.CTkButton(btn_frame, text="Yes", command=on_yes, width=100)
        yes_btn.pack(side="left", padx=10)
        no_btn = customtkinter.CTkButton(btn_frame, text="No", command=on_no, width=100)
        no_btn.pack(side="left", padx=10)
        dialog.grab_set()
        dialog.wait_window()


    def perform_initial_scans(self):
        """Performs the initial data scans after the UI is loaded. (No longer runs scans automatically.)"""
        self.refresh_ocl_profiles_list()
        # Only update status bar if it is initialized
        if hasattr(self, 'status_bar') and self.status_bar:
            self.update_status_bar("Ready.")
        # No automatic scan on startup. User must click scan buttons.

    def start_system_inventory_scan(self, on_finish_callback=None):
        # Only block if a scan is already in progress and this is a user-initiated scan (not a callback chain)
        if self.scan_in_progress and on_finish_callback is None:
            show_custom_messagebox(self, "Scan In Progress", "A scan is already in progress. Please wait for it to complete.", dialog_type="info")
            return
        self.scan_in_progress = True
        self.update_status_bar("Starting System Inventory scan...")
        if self.inventory_scan_button: self.inventory_scan_button.configure(state=customtkinter.DISABLED)
        if self.devenv_audit_button: self.devenv_audit_button.configure(state=customtkinter.DISABLED)

        # Run the scan in a separate thread to keep the UI responsive
        scan_thread = Thread(target=self.run_system_inventory_scan_thread, args=(on_finish_callback,))
        scan_thread.daemon = True
        scan_thread.start()

    def run_system_inventory_scan_thread(self, on_finish_callback=None):
        try:
            self.system_inventory_results = get_installed_software(calculate_disk_usage_flag=True)
            self.after(0, self.update_inventory_display)
        except Exception as e:
            logging.error(f"Error during System Inventory scan: {e}", exc_info=True)
            self.after(0, lambda: self.update_status_bar(f"System Inventory scan failed: {e}", is_error=True))
            # Ensure scan_in_progress is reset even if scan fails
            self.after(0, self.finalize_scan, None)
            return
        self.after(0, self.finalize_scan, on_finish_callback)

    def start_devenv_audit_scan(self, on_finish_callback=None):
        # Only block if a scan is already in progress and this is a user-initiated scan (not a callback chain)
        if self.scan_in_progress and on_finish_callback is None:
            show_custom_messagebox(self, "Scan In Progress", "A scan is already in progress. Please wait for it to complete.", dialog_type="info")
            return

        self.scan_in_progress = True
        self.update_status_bar("Starting Developer Environment Audit...")
        if self.inventory_scan_button: self.inventory_scan_button.configure(state=customtkinter.DISABLED)
        if self.devenv_audit_button: self.devenv_audit_button.configure(state=customtkinter.DISABLED)

        scan_thread = Thread(target=self.run_devenv_audit_scan_thread, args=(on_finish_callback,))
        scan_thread.daemon = True
        scan_thread.start()

    def run_devenv_audit_scan_thread(self, on_finish_callback=None):
        try:
            scanner = EnvironmentScanner()
            (
                self.devenv_components_results,
                self.devenv_env_vars_results,
                self.devenv_issues_results,
            ) = scanner.run_scan() # Corrected method call
            self.after(0, self.update_devenv_audit_display)
        except Exception as e:
            logging.error(f"Error during DevEnv Audit scan: {e}", exc_info=True)
            self.after(0, lambda: self.update_status_bar(f"DevEnv Audit scan failed: {e}", is_error=True))
            # Ensure scan_in_progress is reset even if scan fails
            self.after(0, self.finalize_scan, None)
            return
        self.after(0, self.finalize_scan, on_finish_callback)

    def finalize_scan(self, on_finish_callback=None):
        """
        Finalizes a scan step. If a callback is provided, it executes it (to chain scans).
        If no callback, it means the chain is complete, so re-enable UI elements.
        """
        self.scan_in_progress = False
        if on_finish_callback and callable(on_finish_callback):
            self.update_status_bar("Scan step finished. Starting next scan...", clear_after_ms=3000)
            on_finish_callback()
        else:
            if self.inventory_scan_button: self.inventory_scan_button.configure(state=customtkinter.NORMAL)
            if self.devenv_audit_button: self.devenv_audit_button.configure(state=customtkinter.NORMAL)
            if not IS_WINDOWS and self.inventory_scan_button:
                self.inventory_scan_button.configure(state=customtkinter.DISABLED)
            self.update_status_bar("All scans finished. Ready.", clear_after_ms=5000)

    def update_status_bar(self, message, is_error=False, clear_after_ms=0):
        if not hasattr(self, 'status_bar') or not self.status_bar:
            logging.warning("update_status_bar called before status_bar is initialized.")
            return
        
        default_color = ("#FFFFFF" if customtkinter.get_appearance_mode() == "Dark" else "#000000")
        color = "#FF5555" if is_error else default_color
        self.status_bar.configure(text=message, text_color=color)

        if clear_after_ms > 0:
            def clear_status():
                if self.status_bar:
                    self.status_bar.configure(text="Ready", text_color=default_color)
            self.after(clear_after_ms, clear_status)


    def update_inventory_display(self):
        if not hasattr(self, 'inventory_tree') or not self.inventory_tree:
            return
        inv_cols = ["Name", "Version", "Publisher", "Path", "Size", "Status", "Remarks", "SourceHive", "RegKey"]
        # Clear current rows
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)

        # Filtering
        filter_text = self.inventory_filter_var.get().lower() if hasattr(self, 'inventory_filter_var') else ""
        filtered_results = []
        for item in self.system_inventory_results:
            row = [
                item.get("DisplayName", "N/A"),
                item.get("DisplayVersion", "N/A"),
                item.get("Publisher", "N/A"),
                item.get("InstallLocation", "N/A"),
                item.get("InstallLocationSize", "N/A"),
                item.get("PathStatus", "N/A"),
                item.get("Remarks", ""),
                item.get("SourceHive", "N/A"),
                item.get("RegistryKeyPath", "N/A"),
            ]
            if not filter_text or any(filter_text in str(cell).lower() for cell in row):
                filtered_results.append(row)
        for row in filtered_results:
            self.inventory_tree.insert("", "end", values=row)
        self.update_status_bar(f"System Inventory updated with {len(filtered_results)} items.", clear_after_ms=4000)

    def _sort_inventory_by_column(self, col, reverse):
        if not self.inventory_tree:
            return
        data = []
        for k in self.inventory_tree.get_children(""):
            try:
                v = self.inventory_tree.set(k, col)
            except Exception:
                v = ""
            data.append((v, k))
        def safe_key(val):
            s = str(val[0]) if val[0] is not None else ""
            try:
                return float(s) if s.replace('.', '', 1).isdigit() else s.lower()
            except Exception:
                return s.lower() if hasattr(s, 'lower') else s
        try:
            data.sort(key=safe_key, reverse=reverse)
        except Exception:
            data.sort(key=lambda t: str(t[0]).lower() if t[0] is not None else "", reverse=reverse)
        for index, (val, k) in enumerate(data):
            try:
                self.inventory_tree.move(k, '', index)
            except Exception:
                pass
        self._inventory_sort_column = col
        self._inventory_sort_reverse = not reverse
        for c in self.inventory_tree['columns']:
            txt = c
            if c == col:
                txt += ' ▲' if not reverse else ' ▼'
            self.inventory_tree.heading(c, text=txt, command=lambda c=c: self._sort_inventory_by_column(c, not reverse))

    def _clear_inventory_sort_state(self, event):
        # Remove sort arrows from headings if user clicks elsewhere
        if self._inventory_sort_column and self.inventory_tree:
            for c in self.inventory_tree['columns']:
                self.inventory_tree.heading(c, text=c, command=lambda c=c: self._sort_inventory_by_column(c, False))
            self._inventory_sort_column = None
            self._inventory_sort_reverse = False


    def update_devenv_audit_display(self):
        # Components
        if hasattr(self, 'devenv_components_tree') and self.devenv_components_tree:
            comp_cols = ["ID", "Name", "Category", "Version", "Path", "Executable Path", "Source", "DB Name"]
            for row in self.devenv_components_tree.get_children():
                self.devenv_components_tree.delete(row)
            if self.devenv_components_results:
                for comp in self.devenv_components_results:
                    row = [
                        getattr(comp, 'id', 'N/A'), getattr(comp, 'name', 'N/A'), getattr(comp, 'category', 'N/A'),
                        getattr(comp, 'version', 'N/A') or "N/A", getattr(comp, 'path', 'N/A') or "N/A",
                        getattr(comp, 'executable_path', 'N/A') or "N/A", getattr(comp, 'source_detection', 'N/A') or "N/A", getattr(comp, 'matched_db_name', 'N/A') or "N/A"
                    ]
                    self.devenv_components_tree.insert("", "end", values=row)

        # Env Vars
        if hasattr(self, 'devenv_env_vars_tree') and self.devenv_env_vars_tree:
            env_cols = ["Name", "Value", "Scope"]
            for row in self.devenv_env_vars_tree.get_children():
                self.devenv_env_vars_tree.delete(row)
            if self.devenv_env_vars_results:
                for var in self.devenv_env_vars_results:
                    row = [var.name, var.value, var.scope]
                    self.devenv_env_vars_tree.insert("", "end", values=row)

        # Issues
        if hasattr(self, 'devenv_issues_tree') and self.devenv_issues_tree:
            issue_cols = ["Severity", "Description", "Category", "Component ID", "Related Path"]
            for row in self.devenv_issues_tree.get_children():
                self.devenv_issues_tree.delete(row)
            if self.devenv_issues_results:
                for issue in self.devenv_issues_results:
                    row = [
                        issue.severity, issue.description, issue.category,
                        issue.component_id or "N/A", issue.related_path or "N/A"
                    ]
                    self.devenv_issues_tree.insert("", "end", values=row)
        self.update_status_bar(f"DevEnv Audit updated with {len(self.devenv_components_results)} components and {len(self.devenv_issues_results)} issues.", clear_after_ms=4000)

    def _sort_treeview_by_column(self, tree, col, reverse):
        if not tree:
            return
        data = []
        for k in tree.get_children(""):
            try:
                v = tree.set(k, col)
            except Exception:
                v = ""
            data.append((v, k))
        def safe_key(val):
            s = str(val[0]) if val[0] is not None else ""
            try:
                return float(s) if s.replace('.', '', 1).isdigit() else s.lower()
            except Exception:
                return s.lower() if hasattr(s, 'lower') else s
        try:
            data.sort(key=safe_key, reverse=reverse)
        except Exception:
            data.sort(key=lambda t: str(t[0]).lower() if t[0] is not None else "", reverse=reverse)
        for index, (val, k) in enumerate(data):
            try:
                tree.move(k, '', index)
            except Exception:
                pass
        if not hasattr(tree, '_sort_column'):
            tree._sort_column = None
            tree._sort_reverse = False
        tree._sort_column = col
        tree._sort_reverse = not reverse
        for c in tree['columns']:
            txt = c
            if c == col:
                txt += ' ▲' if not reverse else ' ▼'
            tree.heading(c, text=txt, command=lambda c=c: self._sort_treeview_by_column(tree, c, not reverse))



    def on_ocl_profile_select(self, event):
        # Get selected item from Treeview
        if not self.ocl_profiles_tree:
            return
        selected = self.ocl_profiles_tree.selection()
        if not selected:
            self.selected_ocl_profile_id = None
            if self.ocl_edit_profile_button: self.ocl_edit_profile_button.configure(state="disabled")
            if self.ocl_delete_profile_button: self.ocl_delete_profile_button.configure(state="disabled")
            if self.ocl_export_profile_button: self.ocl_export_profile_button.configure(state="disabled")
            return
        try:
            row_values = self.ocl_profiles_tree.item(selected[0], 'values')
            self.selected_ocl_profile_id = int(row_values[0])
            self.update_status_bar(f"Selected profile ID: {self.selected_ocl_profile_id}")
            profile_obj = ocl_api.get_profile_obj_by_id(self.selected_ocl_profile_id)
            if profile_obj:
                details_str = profile_obj.to_formatted_string()
                if self.ocl_profile_details_text:
                    self.ocl_profile_details_text.configure(state="normal")
                    self.ocl_profile_details_text.delete("1.0", "end")
                    self.ocl_profile_details_text.insert("1.0", details_str)
                    self.ocl_profile_details_text.configure(state="disabled")
                if self.ocl_edit_profile_button: self.ocl_edit_profile_button.configure(state="normal")
                if self.ocl_delete_profile_button: self.ocl_delete_profile_button.configure(state="normal")
                if self.ocl_export_profile_button: self.ocl_export_profile_button.configure(state="normal")
            else:
                self.update_status_bar(f"Could not retrieve details for profile ID {self.selected_ocl_profile_id}", is_error=True)
        except (ValueError, IndexError) as e:
            self.selected_ocl_profile_id = None
            logging.error(f"Error selecting profile: {e}", exc_info=True)
            self.update_status_bar("Error selecting profile.", is_error=True)
            if self.ocl_edit_profile_button: self.ocl_edit_profile_button.configure(state="disabled")
            if self.ocl_delete_profile_button: self.ocl_delete_profile_button.configure(state="disabled")
            if self.ocl_export_profile_button: self.ocl_export_profile_button.configure(state="disabled")

    def _profile_editor_callback(self, updated_profile_obj):
        """Callback function for the profile editor to save/update the profile."""
        try:
            ocl_api.save_or_update_profile(updated_profile_obj)
            self.update_status_bar(f"Profile '{updated_profile_obj.name}' saved successfully.", clear_after_ms=5000)
            self.refresh_ocl_profiles_list()
        except Exception as e:
            logging.error(f"Failed to save profile via callback: {e}", exc_info=True)
            show_custom_messagebox(self, "Save Error", f"An error occurred while saving the profile:\n{e}", "error")

    def create_new_bios_profile(self):
        # Open the HTML BIOS profile editor in the user's default web browser
        import_path = os.path.join(os.path.dirname(__file__), "ocl_module_src", "Bios_Settings_Manager.html")
        if not os.path.exists(import_path):
            show_custom_messagebox(self, "HTML Tool Not Found", f"Could not find Bios_Settings_Manager.html at {import_path}", "error")
            return

        import webbrowser
        webbrowser.open(f"file://{import_path}")

        def import_profile_callback():
            dialog = CTkFileDialog(title="Select Profile JSON File")
            file_path = dialog.get()
            if not file_path:
                return
            try:
                profile_to_import = load_from_json_file(file_path)
                if profile_to_import is None:
                    show_custom_messagebox(self, "Import Error", f"Could not load a valid profile from the selected file.", "error")
                    return
                # Add the profile to the list (via callback)
                self._profile_editor_callback(profile_to_import)
            except Exception as e:
                show_custom_messagebox(self, "Import Error", f"Failed to import profile: {e}", "error")

        # Prompt user to import after browser opens
        import_prompt = customtkinter.CTkToplevel(self)
        import_prompt.title("Import BIOS Profile")
        import_prompt.geometry("400x180")
        label = customtkinter.CTkLabel(import_prompt, text="After saving your profile in the HTML tool, click below to import the .json file.", wraplength=380)
        label.pack(padx=20, pady=(30,10))
        import_button = customtkinter.CTkButton(import_prompt, text="Import Saved Profile (.json)", command=lambda: [import_profile_callback(), import_prompt.destroy()])
        import_button.pack(pady=20)

    def import_bios_profile(self):
        # Corrected CTkFileDialog call
        dialog = CTkFileDialog(title="Select Profile JSON File")
        # The dialog is modal, so execution should pause here until it's closed.
        # The selected path is retrieved from the .get() method.
        file_path = dialog.get()

        if not file_path:
            return
        try:
            profile_to_import = load_from_json_file(file_path)
            if profile_to_import is None:
                show_custom_messagebox(self, "Import Error", f"Could not load a valid profile from the selected file.", "error")
                return
            # Open editor to allow user to review/modify before saving to DB
            editor = OclProfileEditor(self, profile=profile_to_import, callback=self._profile_editor_callback)
            editor.grab_set()
        except Exception as e:
            logging.error(f"Failed to import profile from {file_path}: {e}", exc_info=True)
            show_custom_messagebox(self, "Import Error", f"Failed to import profile: {e}", "error")

    def export_selected_profile(self):
        """Exports the selected profile to a JSON file."""
        if self.selected_ocl_profile_id is None:
            show_custom_messagebox(self, "No Profile Selected", "Please select a profile to export.", "warning")
            return

        try:
            profile_to_export = ocl_api.get_profile_obj_by_id(self.selected_ocl_profile_id)
            if not profile_to_export:
                show_custom_messagebox(self, "Error", f"Could not load profile ID {self.selected_ocl_profile_id} for export.", "error")
                return

            # Ask user for save location using the custom dialog
            dialog = CTkFileDialog(title="Save Profile As...", save=True, save_extension=".json")
            save_path = dialog.get() # This uses the new get() method

            if not save_path:
                return # User cancelled

            # Ensure the file has the correct extension
            if not save_path.lower().endswith('.json'):
                save_path += '.json'

            # Serialize profile and save to file
            profile_dict = profile_to_export.to_html_tool_dict()
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, indent=4)
            
            self.update_status_bar(f"Profile exported to {os.path.basename(save_path)}", clear_after_ms=5000)
            show_custom_messagebox(self, "Export Successful", f"Profile successfully exported to:\n{save_path}", "info")

        except Exception as e:
            logging.error(f"Failed to export profile: {e}", exc_info=True)
            show_custom_messagebox(self, "Export Error", f"An error occurred during export: {e}", "error")

    def edit_selected_profile(self):
        if self.selected_ocl_profile_id is None:
            show_custom_messagebox(self, "No Profile Selected", "Please select a profile from the list to edit.", "warning")
            return
        try:
            # Use the correct API function to get the Profile object
            profile_to_edit = ocl_api.get_profile_obj_by_id(self.selected_ocl_profile_id)
            if profile_to_edit:
                editor = OclProfileEditor(self, profile=profile_to_edit, callback=self._profile_editor_callback)
                editor.grab_set()
            else:
                show_custom_messagebox(self, "Error", f"Could not load profile ID {self.selected_ocl_profile_id} for editing.", "error")
        except Exception as e:
            logging.error(f"Error opening profile editor: {e}", exc_info=True)
            show_custom_messagebox(self, "Editor Error", f"Could not open editor: {e}", "error")

    def delete_selected_profile(self):
        if self.selected_ocl_profile_id is None:
            show_custom_messagebox(self, "No Profile Selected", "Please select a profile from the list to delete.", "warning")
            return
        
        # Confirmation dialog
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile ID {self.selected_ocl_profile_id}?", parent=self)
        if not confirm:
            return

        try:
            # Use the correct API function name
            ocl_api.delete_profile(self.selected_ocl_profile_id)
            self.update_status_bar(f"Profile ID {self.selected_ocl_profile_id} deleted.", clear_after_ms=5000)
            self.selected_ocl_profile_id = None
            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state="normal")
                self.ocl_profile_details_text.delete("1.0", "end")
                self.ocl_profile_details_text.configure(state="disabled")
            if self.ocl_edit_profile_button: self.ocl_edit_profile_button.configure(state="disabled")
            if self.ocl_delete_profile_button: self.ocl_delete_profile_button.configure(state="disabled")
            if self.ocl_export_profile_button: self.ocl_export_profile_button.configure(state="disabled")
            self.refresh_ocl_profiles_list()
        except Exception as e:
            logging.error(f"Failed to delete profile: {e}", exc_info=True)
            show_custom_messagebox(self, "Delete Error", f"Failed to delete profile: {e}", "error")

    def refresh_ocl_profiles_list(self):
        self.update_status_bar("Refreshing OCL Profiles...")
        if not hasattr(self, 'ocl_profiles_tree') or not self.ocl_profiles_tree:
            return
        try:
            # Clear existing rows
            for row in self.ocl_profiles_tree.get_children():
                self.ocl_profiles_tree.delete(row)
            profiles = ocl_api.get_all_profiles() # This returns a list of dicts
            if profiles:
                for profile_dict in profiles:
                    row = [
                        profile_dict.get('id', 'N/A'),
                        profile_dict.get('name', 'N/A'),
                        profile_dict.get('last_modified_date', 'N/A')
                    ]
                    self.ocl_profiles_tree.insert("", "end", values=row)
            self.update_status_bar(f"OCL Profiles refreshed. Found {len(profiles)} profiles.", clear_after_ms=4000)
        except Exception as e:
            logging.error(f"Failed to refresh OCL profiles: {e}", exc_info=True)
            self.update_status_bar(f"Error refreshing OCL profiles: {e}", is_error=True)
        # Debug output for troubleshooting
        logging.info(f"[DevEnvAudit] Components: {type(self.devenv_components_results)} len={len(self.devenv_components_results) if self.devenv_components_results is not None else 'None'}")
        logging.info(f"[DevEnvAudit] Env Vars: {type(self.devenv_env_vars_results)} len={len(self.devenv_env_vars_results) if self.devenv_env_vars_results is not None else 'None'}")
        logging.info(f"[DevEnvAudit] Issues: {type(self.devenv_issues_results)} len={len(self.devenv_issues_results) if self.devenv_issues_results is not None else 'None'}")

    def save_combined_report(self):
        """Saves the collected data to JSON and Markdown files."""
        if self.scan_in_progress:
            show_custom_messagebox(self, "Scan In Progress", "A scan is already in progress. Please wait for it to complete.", dialog_type="info")
            return
        # Directly use the globally managed CTkFileDialog variable
        dialog = CTkFileDialog(
            title="Select Output Directory", open_folder=True
        ) 
        output_dir = dialog.get()

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

    def quit_app(self):
        """Closes the application window."""
        self.destroy()

if __name__ == "__main__":
    # --- Logging Configuration ---
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # --- Main Application Entry Point ---
    app = SystemSageApp()
    app.mainloop()