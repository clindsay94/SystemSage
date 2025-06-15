# %%
# System Sage - Integrated System Utility V2.1

# This script provides system inventory, developer environment auditing,
# and other utilities.
# V2.0:
# - Renamed to SystemSageV2.0.py.
# - Updated internal version references.
# - Includes fixes for OCL API calls.
# - Prepared for application compilation with resource_path helper.
# - Added AI Core module integration (placeholder).
# - Refactored to use CustomTkinter for main window and tabs.
# - Refactored internal tab widgets to CustomTkinter equivalents.
# - Replaced tk.Menu with CTkFrame and CTkButtons for main actions.
# - Replaced OCL Profiles ttk.Treeview with CTkTable.
# - Replaced all ttk.Treeview instances with CTkTable.
# - Replaced tkinter.messagebox with custom CTkDialogs.
# - Replaced filedialog.askdirectory with CTkFileDialog.
# - Added custom theme and font setup.
# - Refined widget styling and layout.
# - Added a fallback mechanism to display a `tkinter` messagebox in case of critical UI errors with CustomTkinter.


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

import customtkinter  # Moved customtkinter import earlier as it's used by placeholder
from CTkTable import CTkTable

# --- DevEnvAudit Imports ---
from devenvaudit_src.scan_logic import EnvironmentScanner
from devenvaudit_src.report_generator import ReportGenerator

# --- OCL Module Imports ---
from ocl_module_src import olb_api as ocl_api


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
        return None


CTkFileDialog = _BaseCTkFileDialogPlaceholder

try:
    from CTkFileDialog.CTkFileDialog import CTkFileDialog as RealCTkFileDialog

    CTkFileDialog = RealCTkFileDialog
    logging.info(
        "Successfully imported real CTkFileDialog from CTkFileDialog.CTkFileDialog"
    )
except ImportError as e_import_ctk:
    logging.warning(
        f"Failed to import real CTkFileDialog from CTkFileDialog.CTkFileDialog: {e_import_ctk}. Placeholder will be used."
    )
except Exception as e_unexpected_import:
    logging.error(
        f"Unexpected error during CTkFileDialog import: {e_unexpected_import}. Placeholder will be used."
    )


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
        IS_WINDOWS = False


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
DEFAULT_LAUNCHER_HINTS = {
    "Steam Game": {"publishers": ["valve"], "paths": ["steamapps"]}
}
COMPONENT_KEYWORDS_FILE = resource_path("systemsage_component_keywords.json")
LAUNCHER_HINTS_FILE = resource_path("systemsage_launcher_hints.json")
COMPONENT_KEYWORDS = load_json_config(
    COMPONENT_KEYWORDS_FILE, DEFAULT_COMPONENT_KEYWORDS
)
LAUNCHER_HINTS = load_json_config(LAUNCHER_HINTS_FILE, DEFAULT_LAUNCHER_HINTS)


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
    if not IS_WINDOWS:
        return "N/A"
    if hkey_root == winreg.HKEY_LOCAL_MACHINE:
        return "HKEY_LOCAL_MACHINE"  # type: ignore
    if hkey_root == winreg.HKEY_CURRENT_USER:
        return "HKEY_CURRENT_USER"  # type: ignore
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
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            "HKLM (64-bit)",
        ),  # type: ignore
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            "HKLM (32-bit)",
        ),  # type: ignore
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            "HKCU",
        ),
    ]  # type: ignore

    for hkey_root, path_suffix, hive_display_name in registry_paths:
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
        self.button_hover_color = (
            "gray70"  # Example, may need adjustment based on theme
        )
        self.action_button_fg_color = "default"  # Or a specific color if needed

        theme_path = resource_path("custom_theme.json")
        if os.path.exists(theme_path):
            customtkinter.set_default_color_theme(theme_path)
            logging.info(f"Successfully loaded custom theme from {theme_path}")
        else:
            customtkinter.set_default_color_theme("dark-blue")
            logging.info("Using default 'dark-blue' theme.")

        self.default_font = ("Roboto", 12)
        self.button_font = ("Roboto", 12, "bold")
        self.title_font = ("Roboto", 14, "bold")  # Font for section titles
        self.option_add("*Font", self.default_font)
        self.title("System Sage V2.0")
        self.geometry("1200x850")

        self.inventory_scan_button = None
        self.devenv_audit_button = None

        self.inventory_table = None
        self.devenv_components_table = None
        self.devenv_env_vars_table = None
        self.devenv_issues_table = None

        self.ocl_profiles_table = None
        self.selected_ocl_profile_id = None
        self.status_bar = None  # Initialize as None

        self.scan_in_progress = False
        self.system_inventory_results = []
        self.devenv_components_results = []
        self.devenv_env_vars_results = []
        self.devenv_issues_results = []

        self.ocl_profile_details_text = None
        self.ocl_refresh_button = None
        self.ocl_save_new_button = None
        self.ocl_update_selected_button = None
        self.ocl_edit_profile_button = None  # New button

        self._setup_ui()
        if not IS_WINDOWS:
            self.after(100, self.start_system_inventory_scan)

    def _setup_ui(self):
        # Action Bar
        self.action_bar_frame = customtkinter.CTkFrame(
            self, corner_radius=0, height=50, border_width=0
        )
        self.action_bar_frame.pack(
            side=tk.TOP, fill=tk.X, padx=0, pady=(0, self.padding_std)
        )

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

        # Main TabView
        self.main_notebook = customtkinter.CTkTabview(
            self, corner_radius=self.corner_radius_soft, border_width=0
        )
        self.main_notebook.pack(
            expand=True,
            fill="both",
            padx=self.padding_large,
            pady=(self.padding_std, self.padding_large),
        )
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
            pady=(self.padding_std, self.padding_large),
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
        ocl_tab_frame = self.main_notebook.tab("Overclocker's Logbook")
        ocl_tab_frame.grid_columnconfigure(0, weight=1)
        ocl_tab_frame.grid_rowconfigure(0, weight=2)
        ocl_tab_frame.grid_rowconfigure(1, weight=1)

        ocl_top_frame = customtkinter.CTkFrame(
            ocl_tab_frame, corner_radius=self.corner_radius_soft, border_width=1
        )
        ocl_top_frame.grid(
            row=0,
            column=0,
            padx=self.padding_large,
            pady=(self.padding_large, self.padding_std),
            sticky="nsew",
        )
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
            command=self.on_ocl_profile_select_ctktable,
            font=self.default_font,
            corner_radius=self.corner_radius_std,
            hover_color=self.button_hover_color,
        )
        self.ocl_profiles_table.pack(
            expand=True, fill="both", padx=self.padding_std, pady=self.padding_std
        )

        ocl_bottom_frame = customtkinter.CTkFrame(
            ocl_tab_frame, corner_radius=self.corner_radius_soft, border_width=1
        )
        ocl_bottom_frame.grid(
            row=1,
            column=0,
            padx=self.padding_large,
            pady=(self.padding_std, self.padding_large),
            sticky="nsew",
        )
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

        actions_ctk_frame = customtkinter.CTkFrame(
            ocl_bottom_frame, fg_color="transparent", border_width=0
        )
        actions_ctk_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=self.padding_large,
            pady=(self.padding_std, self.padding_large),
        )

        self.ocl_refresh_button = customtkinter.CTkButton(
            master=actions_ctk_frame,
            text="Refresh Profile List",
            command=self.refresh_ocl_profiles_list,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            hover_color=self.button_hover_color,
        )
        self.ocl_refresh_button.pack(
            side=tk.LEFT, padx=(0, self.padding_std), pady=self.padding_std
        )

        self.ocl_save_new_button = customtkinter.CTkButton(
            master=actions_ctk_frame,
            text="Save System as New Profile",
            command=self.save_system_as_new_ocl_profile,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            hover_color=self.button_hover_color,
        )
        self.ocl_save_new_button.pack(
            side=tk.LEFT, padx=self.padding_std, pady=self.padding_std
        )

        self.ocl_update_selected_button = customtkinter.CTkButton(
            master=actions_ctk_frame,
            text="Add Log Entry",
            command=self.update_selected_ocl_profile,  # Renamed
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            hover_color=self.button_hover_color,
        )
        self.ocl_update_selected_button.pack(
            side=tk.LEFT, padx=self.padding_std, pady=self.padding_std
        )

        self.ocl_edit_profile_button = customtkinter.CTkButton(
            master=actions_ctk_frame,
            text="Edit Profile",
            command=self.edit_selected_ocl_profile,
            font=self.button_font,
            corner_radius=self.corner_radius_soft,
            hover_color=self.button_hover_color,
        )
        self.ocl_edit_profile_button.pack(
            side=tk.LEFT, padx=self.padding_std, pady=self.padding_std
        )

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
            self.after(0, self.update_inventory_display, software_list)
            self.save_system_inventory_report(software_list)  # Call the new save method
        except Exception as e:
            logging.error(
                f"Error in system inventory thread: {e}\n{traceback.format_exc()}"
            )
            self.after(0, self.inventory_scan_error, e)

    def save_system_inventory_report(self, software_list):
        output_dir = "output_data/system_inventory/"
        try:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"system_inventory_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            full_path = os.path.join(output_dir, filename)

            # Prepare data for JSON dump. software_list is a list of dictionaries.
            # We can wrap it for consistency or add metadata.
            report_data = {
                "reportTime": datetime.datetime.now().isoformat(),
                "systemInventory": software_list,
            }

            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=4)

            logging.info(f"System inventory report successfully saved to {full_path}")

        except Exception as e:
            logging.error(
                f"Failed to save system inventory report to {output_dir}: {e}",
                exc_info=True,
            )

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

        self.system_inventory_results = software_list
        status_msg = (
            f"System Inventory Scan Complete. Found {len(software_list)} items."
        )
        if (
            len(software_list) == 1
            and software_list[0].get("Category") == "Informational"
        ):
            status_msg = software_list[0].get("Remarks")
        if self.status_bar:
            self.status_bar.configure(text=status_msg)
        self.finalize_scan_ui_state()

    def inventory_scan_error(self, error):
        show_custom_messagebox(
            self,
            "Scan Error",
            f"An error occurred during System Inventory: {error}",
            dialog_type="error",
        )
        if self.status_bar:
            self.status_bar.configure(text="System Inventory Scan Failed.")
        self.finalize_scan_ui_state()

    def _devenv_status_callback(self, message):
        if self.status_bar:
            self.status_bar.configure(text=f"[DevEnvAudit] {message}")
        logging.info(f"[DevEnvAudit Status] {message}")

    def _devenv_progress_callback(self, current, total, message):
        if self.status_bar:
            self.status_bar.configure(
                text=f"[DevEnvAudit Progress] {current}/{total}: {message}"
            )
        logging.info(f"[DevEnvAudit Progress] {current}/{total}: {message}")

    def start_devenv_audit_scan(self):
        if self.scan_in_progress:
            show_custom_messagebox(
                self,
                "Scan In Progress",
                "A scan is already running.",
                dialog_type="warning",
            )
            return
        self.scan_in_progress = True
        if self.status_bar:
            self.status_bar.configure(text="Starting Developer Environment Audit...")
        self._update_action_buttons_state(customtkinter.DISABLED)
        if self.devenv_components_table:
            self.devenv_components_table.delete_rows(
                list(range(len(self.devenv_components_table.values)))
            )
        if self.devenv_env_vars_table:
            self.devenv_env_vars_table.delete_rows(
                list(range(len(self.devenv_env_vars_table.values)))
            )
        if self.devenv_issues_table:
            self.devenv_issues_table.delete_rows(
                list(range(len(self.devenv_issues_table.values)))
            )

        thread = Thread(target=self.run_devenv_audit_thread, daemon=True)
        thread.start()

    def run_devenv_audit_thread(self):
        try:
            scanner = EnvironmentScanner(
                progress_callback=self._devenv_progress_callback,
                status_callback=self._devenv_status_callback,
            )
            components, env_vars, issues = scanner.run_scan()
            self.after(
                0, self.update_devenv_audit_display, components, env_vars, issues
            )
            self.save_devenv_audit_report(
                components, env_vars, issues
            )  # Call the new save method
        except Exception as e:
            logging.error(f"DevEnvAudit scan failed: {e}\n{traceback.format_exc()}")
            self.after(0, self.devenv_scan_error, e)

    def update_devenv_audit_display(self, components, env_vars, issues):
        if self.devenv_components_table:
            # Original: header = ["ID", "Name", "Category", "Version", "Path", "Executable Path"]
            header = [
                "ID",
                "Name",
                "Category",
                "Version",
                "Path",
                "Executable Path",
                "Source",
                "DB Name",
            ]  # Updated header
            table_values = [header]
            if components:
                for comp in components:
                    table_values.append(
                        [
                            str(comp.id),
                            str(comp.name),
                            str(comp.category),
                            str(comp.version),
                            str(comp.path),
                            str(comp.executable_path),
                            str(comp.source_detection),  # Added new field
                            str(comp.matched_db_name),  # Added new field
                        ]
                    )
            else:
                # Ensure placeholder matches new column count
                table_values.append(
                    ["No components detected.", "", "", "", "", "", "", ""]
                )
            self.devenv_components_table.update_values(table_values)

        if self.devenv_env_vars_table:
            header = ["Name", "Value", "Scope"]
            table_values = [header]
            if env_vars:
                for ev in env_vars:
                    table_values.append([str(ev.name), str(ev.value), str(ev.scope)])
            else:
                table_values.append(["No environment variables found.", "", ""])
            self.devenv_env_vars_table.update_values(table_values)

        if self.devenv_issues_table:
            header = [
                "Severity",
                "Description",
                "Category",
                "Component ID",
                "Related Path",
            ]
            table_values = [header]
            if issues:
                for issue in issues:
                    table_values.append(
                        [
                            str(issue.severity),
                            str(issue.description),
                            str(issue.category),
                            str(issue.component_id),
                            str(issue.related_path),
                        ]
                    )
            else:
                table_values.append(["No issues identified.", "", "", "", ""])
            self.devenv_issues_table.update_values(table_values)

        self.devenv_components_results = components
        self.devenv_env_vars_results = env_vars
        self.devenv_issues_results = issues
        self.finalize_devenv_scan(
            f"DevEnv Audit Complete. Found {len(components)} components, {len(env_vars)} env vars, {len(issues)} issues."
        )

    def save_devenv_audit_report(self, components, env_vars, issues):
        output_dir = "output_data/devenv_audit/"
        try:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"devenv_audit_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            full_path = os.path.join(output_dir, filename)

            # Instantiate ReportGenerator
            report_generator = ReportGenerator(
                detected_components=components,
                environment_variables=env_vars,
                issues=issues,
            )

            # Export to JSON
            report_generator.export_to_json(
                full_path
            )  # ReportGenerator's method already logs success/failure detail

            logging.info(
                f"DevEnv audit report successfully initiated for saving to {full_path}"
            )

        except Exception as e:
            logging.error(
                f"Failed to save DevEnv audit report to {output_dir}: {e}",
                exc_info=True,
            )
            # Optionally, inform the user via UI if this is critical
            # self.after(0, show_custom_messagebox, self, "Save Error", f"Failed to save DevEnv audit report: {e}", "error")

    def devenv_scan_error(self, error):
        show_custom_messagebox(
            self,
            "DevEnv Audit Error",
            f"An error occurred: {error}",
            dialog_type="error",
        )
        self.finalize_devenv_scan("DevEnv Audit Failed.")

    def finalize_devenv_scan(self, message="DevEnv Audit Finished."):
        if self.status_bar:
            self.status_bar.configure(text=message)
        self.finalize_scan_ui_state()

    def refresh_ocl_profiles_list(self):
        logging.info("SystemSageApp.refresh_ocl_profiles_list called")
        try:
            if self.ocl_profiles_table:
                profiles_data = ocl_api.get_all_profiles()
                table_values = [["ID", "Profile Name", "Last Modified"]]
                if profiles_data:
                    for profile in profiles_data:
                        table_values.append(
                            [
                                str(profile.get("id", "N/A")),
                                str(profile.get("name", "N/A")),
                                str(profile.get("last_modified_date", "N/A")),
                            ]
                        )
                else:
                    table_values.append(["No profiles found.", "", ""])
                self.ocl_profiles_table.update_values(table_values)
            if self.status_bar:
                self.status_bar.configure(text="OCL Profiles refreshed.")
            self.selected_ocl_profile_id = None
            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                self.ocl_profile_details_text.delete("0.0", tk.END)
                self.ocl_profile_details_text.insert(
                    "0.0", "Select a profile to view details."
                )
                self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)
        except Exception as e:
            show_custom_messagebox(
                self,
                "OCL Error",
                f"Failed to refresh OCL profiles: {e}",
                dialog_type="error",
            )
            logging.error(f"Failed to refresh OCL profiles: {e}", exc_info=True)
            if self.status_bar:
                self.status_bar.configure(text="OCL Profile refresh failed.")

    def save_system_as_new_ocl_profile(self):
        # 1. Get Profile Name
        name_dialog = customtkinter.CTkInputDialog(
            text="Enter Profile Name:", title="New OCL Profile - Name"
        )
        profile_name = name_dialog.get_input()
        if not profile_name:
            show_custom_messagebox(
                self,
                "Cancelled",
                "New profile creation cancelled: No name provided.",
                dialog_type="info",
            )
            if self.status_bar:
                self.status_bar.configure(text="New OCL profile creation cancelled.")
            return

        # 2. Get Profile Description
        desc_dialog = customtkinter.CTkInputDialog(
            text="Enter Profile Description:", title="New OCL Profile - Description"
        )
        profile_description = desc_dialog.get_input()
        if profile_description is None:  # Cancelled
            profile_description = (
                "No description."  # Default if cancelled, but not if empty string given
            )
        elif not profile_description.strip():  # Empty string or whitespace
            profile_description = "No description provided."

        # 3. Loop for settings
        initial_settings = []
        while True:
            add_setting_dialog = customtkinter.CTkInputDialog(
                text="Add a new setting? (yes/no)",
                title="New OCL Profile - Add Setting",
            )
            add_setting_choice = add_setting_dialog.get_input()

            if add_setting_choice is None or add_setting_choice.lower() != "yes":
                break  # Break if cancelled or not 'yes'

            category_dialog = customtkinter.CTkInputDialog(
                text="Enter Setting Category (e.g., CPU, Memory):",
                title="New Setting - Category",
            )
            setting_category = category_dialog.get_input()
            if not setting_category:  # Cancelled or empty
                show_custom_messagebox(
                    self,
                    "Info",
                    "Setting input cancelled or empty. Stopping setting additions.",
                    dialog_type="info",
                )
                break

            name_dialog = customtkinter.CTkInputDialog(
                text="Enter Setting Name (e.g., Core Clock, Voltage):",
                title="New Setting - Name",
            )
            setting_name = name_dialog.get_input()
            if not setting_name:  # Cancelled or empty
                show_custom_messagebox(
                    self,
                    "Info",
                    "Setting input cancelled or empty. Stopping setting additions.",
                    dialog_type="info",
                )
                break

            value_dialog = customtkinter.CTkInputDialog(
                text="Enter Setting Value (e.g., 4.5 GHz, 1.25v):",
                title="New Setting - Value",
            )
            setting_value = value_dialog.get_input()
            if (
                setting_value is None
            ):  # Check for explicit cancel, empty string is a valid value
                show_custom_messagebox(
                    self,
                    "Info",
                    "Setting input cancelled. Stopping setting additions.",
                    dialog_type="info",
                )
                break

            type_dialog = customtkinter.CTkInputDialog(
                text="Enter Value Type (str, int, float, bool):",
                title="New Setting - Value Type",
            )
            value_type = type_dialog.get_input()
            if not value_type:  # Cancelled or empty
                value_type = "str"  # Default to string

            initial_settings.append(
                {
                    "category": setting_category,
                    "setting_name": setting_name,
                    "setting_value": setting_value,
                    "value_type": value_type,
                }
            )
            show_custom_messagebox(
                self,
                "Setting Added",
                f"Setting '{setting_name}' added to profile.",
                dialog_type="info",
            )

        # Ask to include hardware snapshot
        snapshot_dialog = customtkinter.CTkInputDialog(
            text="Include current system hardware snapshot in this profile? (yes/no)",
            title="Hardware Snapshot",
        )
        snapshot_choice = snapshot_dialog.get_input()

        if snapshot_choice and snapshot_choice.lower() == "yes":
            is_placeholder_inventory = (
                len(self.system_inventory_results) == 1
                and self.system_inventory_results[0].get("Category") == "Informational"
            )
            if self.system_inventory_results and not is_placeholder_inventory:
                logging.info(
                    f"Attempting to add hardware snapshot to OCL profile '{profile_name}'."
                )
                snapshot_added = False
                # Attempt to find CPU info
                for item in self.system_inventory_results:
                    if (
                        "processor" in item.get("DisplayName", "").lower()
                        or "cpu" in item.get("DisplayName", "").lower()
                    ):
                        initial_settings.append(
                            {
                                "category": "HardwareSnapshot",
                                "setting_name": "CPU_Info",
                                "setting_value": item.get("DisplayName"),
                                "value_type": "str",
                            }
                        )
                        snapshot_added = True
                        logging.info(
                            f"Added CPU info from snapshot: {item.get('DisplayName')}"
                        )
                        break
                # Attempt to find GPU info
                for item in self.system_inventory_results:
                    dn_lower = item.get("DisplayName", "").lower()
                    if (
                        "nvidia" in dn_lower
                        or "amd radeon" in dn_lower
                        or "intel graphics" in dn_lower
                        or "display adapter" in dn_lower
                    ):
                        initial_settings.append(
                            {
                                "category": "HardwareSnapshot",
                                "setting_name": "GPU_Info",
                                "setting_value": item.get("DisplayName"),
                                "value_type": "str",
                            }
                        )
                        snapshot_added = True
                        logging.info(
                            f"Added GPU info from snapshot: {item.get('DisplayName')}"
                        )
                        break

                initial_settings.append(
                    {
                        "category": "HardwareSnapshot",
                        "setting_name": "OS_Version",
                        "setting_value": platform.platform(),
                        "value_type": "str",
                    }
                )
                logging.info(f"Added OS version from snapshot: {platform.platform()}")
                snapshot_added = True

                if (
                    not snapshot_added
                ):  # If specific items weren't found but we have some inventory
                    initial_settings.append(
                        {
                            "category": "HardwareSnapshot",
                            "setting_name": "Details",
                            "setting_value": "Snapshot taken, specific components to be listed by enhancing System Inventory data.",
                            "value_type": "str",
                        }
                    )
                    logging.info(
                        "Added generic hardware snapshot note as specific CPU/GPU info was not found in inventory."
                    )
                else:
                    show_custom_messagebox(
                        self,
                        "Snapshot Added",
                        "Hardware snapshot details added to the profile.",
                        dialog_type="info",
                    )

            elif is_placeholder_inventory:
                logging.info(
                    "Hardware snapshot skipped: System Inventory data is placeholder (e.g., non-Windows OS)."
                )
                show_custom_messagebox(
                    self,
                    "Snapshot Skipped",
                    "Hardware snapshot skipped: System Inventory data is placeholder or not applicable.",
                    dialog_type="info",
                )
            else:
                logging.info(
                    "Hardware snapshot skipped: No System Inventory data available."
                )
                show_custom_messagebox(
                    self,
                    "Snapshot Skipped",
                    "Hardware snapshot skipped: No System Inventory data available. Please run a scan first.",
                    dialog_type="warning",
                )
        else:
            logging.info("User chose not to include hardware snapshot.")

        # 4. Call ocl_api.create_new_profile
        success = False
        profile_id = None  # Initialize profile_id to ensure it's always bound
        try:
            # Assuming initial_logs can be a simple creation message or an empty list if settings are the primary focus
            initial_logs = [
                f"Profile '{profile_name}' created with {len(initial_settings)} initial settings."
            ]
            if not initial_settings:
                initial_logs = ["Profile created with no initial settings."]

            profile_id = ocl_api.create_new_profile(
                name=profile_name,
                description=profile_description,
                initial_settings=initial_settings,
                initial_logs=initial_logs,
            )
            success = profile_id is not None
            if success:
                show_custom_messagebox(
                    self,
                    "Success",
                    f"New OCL profile '{profile_name}' saved with ID: {profile_id}.\n{len(initial_settings)} settings included.",
                    dialog_type="info",
                )
                logging.info(
                    f"New OCL profile '{profile_name}' (ID: {profile_id}) created with description '{profile_description}' and {len(initial_settings)} settings."
                )
                self.refresh_ocl_profiles_list()
            else:
                show_custom_messagebox(
                    self,
                    "Error",
                    f"Failed to save new OCL profile '{profile_name}'. API did not return an ID.",
                    dialog_type="error",
                )
                logging.error(
                    f"Failed to save new OCL profile '{profile_name}'. API returned no ID. Description: '{profile_description}', Settings attempted: {len(initial_settings)}"
                )
        except Exception as e:
            show_custom_messagebox(
                self,
                "OCL API Error",
                f"Error saving profile '{profile_name}': {e}",
                dialog_type="error",
            )
            logging.error(
                f"OCL save error for profile '{profile_name}': {e}", exc_info=True
            )
        if self.status_bar:
            status_message = (
                f"Save new OCL profile '{profile_name}' attempt. Success: {success}"
            )
            if success:  # If success is True, profile_id is guaranteed to be non-None and hold the ID
                status_message += f" (ID: {profile_id})"
            self.status_bar.configure(text=status_message)
            self.status_bar.configure(text=status_message)

    def _reselect_ocl_profile_after_update(self):
        """Helper to re-select the current OCL profile in the table and update details."""
        row_to_select = 0  # Default to first data row if ID not found or None
        if (
            self.selected_ocl_profile_id is not None
            and self.ocl_profiles_table
            and hasattr(self.ocl_profiles_table, "values")
            and len(self.ocl_profiles_table.values) > 1
        ):  # Check if there are data rows
            try:
                # Iterate through data rows (skip header at index 0)
                for i, row_data in enumerate(self.ocl_profiles_table.values[1:]):
                    # Ensure row_data is not empty and has at least one element (the ID)
                    if (
                        row_data
                        and len(row_data) > 0
                        and str(row_data[0]) == str(self.selected_ocl_profile_id)
                    ):
                        row_to_select = i  # i is the 0-based index of the data row
                        logging.info(
                            f"Found profile ID {self.selected_ocl_profile_id} at data row index {i} for reselection."
                        )
                        break
                else:  # Loop completed without break
                    logging.warning(
                        f"Profile ID {self.selected_ocl_profile_id} not found in table for reselection. Defaulting to row 0."
                    )
            except Exception as e_reselect:
                logging.error(
                    f"Error finding row for reselection of profile ID {self.selected_ocl_profile_id}: {e_reselect}"
                )
        elif self.selected_ocl_profile_id is None:
            logging.info("No profile ID selected; reselecting default row 0.")
        else:
            logging.info(
                "OCL profiles table not ready or empty; reselecting default row 0."
            )

        self.on_ocl_profile_select_ctktable({"row": row_to_select})

    def edit_selected_ocl_profile(self):
        if self.selected_ocl_profile_id is None:
            show_custom_messagebox(
                self,
                "No Profile Selected",
                "Please select an OCL profile from the table to edit.",
                dialog_type="warning",
            )
            if self.status_bar:
                self.status_bar.configure(text="Edit OCL profile: No profile selected.")
            return

        if self.status_bar:
            self.status_bar.configure(
                text=f"Editing OCL profile ID: {self.selected_ocl_profile_id}..."
            )
        logging.info(
            f"Starting edit for OCL profile ID: {self.selected_ocl_profile_id}"
        )

        details = ocl_api.get_profile_details(self.selected_ocl_profile_id)
        if not details:
            show_custom_messagebox(
                self,
                "Error",
                f"Could not fetch details for profile ID: {self.selected_ocl_profile_id}.",
                dialog_type="error",
            )
            if self.status_bar:
                self.status_bar.configure(
                    text=f"Edit OCL profile: Failed to fetch details for ID {self.selected_ocl_profile_id}."
                )
            logging.error(
                f"Failed to fetch details for OCL profile ID {self.selected_ocl_profile_id} during edit."
            )
            return

        current_name = details.get("name", "")
        current_description = details.get("description", "")
        current_settings = details.get("settings", [])

        # Edit Name
        name_dialog = customtkinter.CTkInputDialog(
            text=f"Enter new Profile Name.\nCurrent: {current_name}",
            title="Edit Profile Name",
        )
        new_name = name_dialog.get_input()
        if new_name is None:  # User cancelled
            show_custom_messagebox(
                self,
                "Cancelled",
                "Profile edit cancelled during name input.",
                dialog_type="info",
            )
            if self.status_bar:
                self.status_bar.configure(text="OCL profile edit cancelled.")
            return
        if not new_name.strip():  # User entered empty string
            show_custom_messagebox(
                self,
                "Validation Error",
                "Profile name cannot be empty.",
                dialog_type="warning",
            )
            if self.status_bar:
                self.status_bar.configure(
                    text="OCL profile edit: Name cannot be empty."
                )
            return

        # Edit Description
        desc_dialog = customtkinter.CTkInputDialog(
            text=f"Enter new Profile Description.\nCurrent: {current_description}",
            title="Edit Profile Description",
        )
        new_description = desc_dialog.get_input()
        if new_description is None:  # User cancelled
            new_description = current_description  # Keep original if cancelled
        elif not new_description.strip():
            new_description = "No description provided."

        settings_to_add = []
        settings_to_update = []
        setting_ids_to_delete = []

        # Display current settings (simplified for this subtask - using logging)
        logging.info(
            "Current settings for profile ID %s:", self.selected_ocl_profile_id
        )
        if not current_settings:
            logging.info("  No settings currently exist for this profile.")
        for setting in current_settings:
            logging.info(
                f"  ID: {setting.get('id')}, Category: {setting.get('category')}, Name: {setting.get('setting_name')}, Value: {setting.get('setting_value')}, Type: {setting.get('value_type')}"
            )

        show_custom_messagebox(
            self,
            "Settings Overview",
            "Current settings have been logged to the console/log file. Please review them there before proceeding with actions in the upcoming dialogs.",
            dialog_type="info",
        )

        # Loop through existing settings for actions
        for setting in current_settings:
            setting_id = setting.get("id")
            action_dialog = customtkinter.CTkInputDialog(
                text=f"Action for '{setting.get('category')} - {setting.get('setting_name')}: {setting.get('setting_value')}' (ID: {setting_id})?\n(keep/update/delete/skip all)",
                title="Edit Setting Action",
            )
            action = action_dialog.get_input()

            if action is None:
                action = "keep"  # Default to keep if dialog is closed

            action_lower = action.lower()
            if action_lower == "update":
                new_value_dialog = customtkinter.CTkInputDialog(
                    text=f"Enter new Setting Value.\nCurrent: {str(setting.get('setting_value'))}",
                    title="Update Setting Value",
                )
                new_value = new_value_dialog.get_input()
                if new_value is not None:  # Allow empty string as a value
                    settings_to_update.append(
                        {"id": setting_id, "setting_value": new_value}
                    )
                    # Not prompting for value_type change for simplicity
                else:  # Cancelled value update
                    show_custom_messagebox(
                        self,
                        "Info",
                        f"Update for setting ID {setting_id} cancelled. Kept original value.",
                        dialog_type="info",
                    )
            elif action_lower == "delete":
                setting_ids_to_delete.append(setting_id)
            elif action_lower == "skip all":
                break
            # Else ('keep' or anything else): do nothing

        # Add new settings
        while True:
            add_new_dialog = customtkinter.CTkInputDialog(
                text="Add a completely new setting to this profile? (yes/no)",
                title="Add New Setting",
            )
            add_new_choice = add_new_dialog.get_input()
            if add_new_choice is None or add_new_choice.lower() != "yes":
                break

            category_dialog = customtkinter.CTkInputDialog(
                text="Enter New Setting Category:", title="New Setting - Category"
            )
            s_cat = category_dialog.get_input()
            if not s_cat:
                break
            name_dialog = customtkinter.CTkInputDialog(
                text="Enter New Setting Name:", title="New Setting - Name"
            )
            s_name = name_dialog.get_input()
            if not s_name:
                break
            value_dialog = customtkinter.CTkInputDialog(
                text="Enter New Setting Value:", title="New Setting - Value"
            )
            s_val = value_dialog.get_input()
            if not s_val:
                break
            type_dialog = customtkinter.CTkInputDialog(
                text="Enter New Setting Type:", title="New Setting - Type"
            )
            s_type = type_dialog.get_input()
            if not s_type:
                s_type = "str"

            settings_to_add.append(
                {
                    "category": s_cat,
                    "setting_name": s_name,
                    "setting_value": s_val,
                    "value_type": s_type,
                }
            )
            show_custom_messagebox(
                self,
                "Setting Added",
                f"New setting '{s_name}' queued for addition.",
                dialog_type="info",
            )

        # API Call
        update_success = False
        try:
            update_success = ocl_api.update_existing_profile(
                profile_id=self.selected_ocl_profile_id,
                name=new_name,
                description=new_description,
                settings_to_add=settings_to_add,
                settings_to_update=settings_to_update,
                setting_ids_to_delete=setting_ids_to_delete,
            )
            if update_success:
                show_custom_messagebox(
                    self,
                    "Success",
                    f"OCL Profile ID {self.selected_ocl_profile_id} updated successfully.",
                    dialog_type="info",
                )
                logging.info(
                    f"OCL Profile ID {self.selected_ocl_profile_id} updated. Name: '{new_name}', Desc: '{new_description}', Added: {len(settings_to_add)}, Updated: {len(settings_to_update)}, Deleted: {len(setting_ids_to_delete)}"
                )
                self.refresh_ocl_profiles_list()  # Refresh list and details display
                # Explicitly re-select and show details for the updated profile
                self.after(100, self._reselect_ocl_profile_after_update)

            else:
                show_custom_messagebox(
                    self,
                    "Error",
                    f"Failed to update OCL profile ID {self.selected_ocl_profile_id}. API returned failure.",
                    dialog_type="error",
                )
                logging.error(
                    f"Failed to update OCL profile ID {self.selected_ocl_profile_id}. API returned False."
                )
        except Exception as e:
            show_custom_messagebox(
                self,
                "API Error",
                f"Error updating profile ID {self.selected_ocl_profile_id}: {e}",
                dialog_type="error",
            )
            logging.error(
                f"API error updating OCL profile ID {self.selected_ocl_profile_id}: {e}",
                exc_info=True,
            )

        if self.status_bar:
            self.status_bar.configure(
                text=f"OCL Profile ID {self.selected_ocl_profile_id} update attempt. Success: {update_success}"
            )

    def update_selected_ocl_profile(self):  # Method now handles different log types
        if self.selected_ocl_profile_id is None:
            show_custom_messagebox(
                self,
                "No Profile Selected",
                "Please select a profile to add a log to.",
                dialog_type="warning",
            )
            if self.status_bar:
                self.status_bar.configure(text="Add Log: No profile selected.")
            return

        profile_id = self.selected_ocl_profile_id
        log_text_to_add = None  # Initialize here
        log_type_dialog = customtkinter.CTkInputDialog(
            text="What type of log? (note/stability)", title="Select Log Type"
        )
        log_type = log_type_dialog.get_input()

        if log_type is None:  # Cancelled
            show_custom_messagebox(
                self, "Cancelled", "Add log operation cancelled.", dialog_type="info"
            )
            if self.status_bar:
                self.status_bar.configure(text="Add Log: Cancelled.")
            return

        log_type_lower = log_type.lower()

        if log_type_lower == "note":
            note_dialog = customtkinter.CTkInputDialog(
                text="Enter Note Text:", title="Add Note Log"
            )
            note_text = note_dialog.get_input()
            if note_text:  # Allow empty notes if user presses OK, but not if cancelled.
                log_text_to_add = f"Note: {note_text}"
            elif note_text is None:  # Cancelled
                show_custom_messagebox(
                    self, "Cancelled", "Add note log cancelled.", dialog_type="info"
                )
                if self.status_bar:
                    self.status_bar.configure(text="Add Log (Note): Cancelled.")
                return
            else:  # Empty string given
                log_text_to_add = "Note: (Empty note)"
        elif log_type_lower == "stability":
            test_name_dialog = customtkinter.CTkInputDialog(
                text="Test Name/Type (e.g., Prime95 Small FFTs):",
                title="Stability Log - Test Name",
            )
            test_name = test_name_dialog.get_input()
            if not test_name:  # Cancelled or empty
                show_custom_messagebox(
                    self,
                    "Cancelled",
                    "Stability log cancelled: Test Name required.",
                    dialog_type="info",
                )
                if self.status_bar:
                    self.status_bar.configure(
                        text="Add Log (Stability): Cancelled - Test Name."
                    )
                return

            duration_dialog = customtkinter.CTkInputDialog(
                text="Duration (e.g., 1 hour):", title="Stability Log - Duration"
            )
            duration = duration_dialog.get_input() or "N/A"

            max_temp_dialog = customtkinter.CTkInputDialog(
                text="Max Temperature (e.g., 85C):", title="Stability Log - Max Temp"
            )
            max_temp = max_temp_dialog.get_input() or "N/A"

            errors_dialog = customtkinter.CTkInputDialog(
                text="Errors Encountered (e.g., 0, 2 errors):",
                title="Stability Log - Errors",
            )
            errors = errors_dialog.get_input() or "N/A"

            result_dialog = customtkinter.CTkInputDialog(
                text="Result (Pass/Fail):", title="Stability Log - Result"
            )
            result = result_dialog.get_input() or "N/A"

            log_text_to_add = f"Stability Test: {test_name} - Duration: {duration}, Max Temp: {max_temp}, Errors: {errors}, Result: {result}"
        else:
            show_custom_messagebox(
                self,
                "Invalid Type",
                f"Invalid log type '{log_type}' selected. Please choose 'note' or 'stability'.",
                dialog_type="warning",
            )
            if self.status_bar:
                self.status_bar.configure(text=f"Add Log: Invalid type '{log_type}'.")
            return

        # Check if log_text_to_add was successfully populated by the log type branches
        if log_text_to_add is not None:
            success = False
            try:
                log_id = ocl_api.add_log_to_profile(
                    profile_id=profile_id, log_text=log_text_to_add
                )
                success = log_id is not None
                if success:
                    show_custom_messagebox(
                        self,
                        "Log Added",
                        f"Log entry added to OCL profile ID {profile_id} (Log ID: {log_id}).",
                        dialog_type="info",
                    )
                    logging.info(
                        f"Log entry of type '{log_type_lower}' added to OCL profile ID {profile_id}. Log: '{log_text_to_add}'"
                    )
                    self.refresh_ocl_profiles_list()
                    # Re-select and show details for the updated profile
                    self.after(100, self._reselect_ocl_profile_after_update)
                else:
                    show_custom_messagebox(
                        self,
                        "Error",
                        f"Failed to add log to OCL profile ID {profile_id}. API returned no log ID.",
                        dialog_type="error",
                    )
                    logging.error(
                        f"Failed to add log to OCL profile ID {profile_id}. Log text: {log_text_to_add}"
                    )
            except Exception as e:
                show_custom_messagebox(
                    self,
                    "OCL API Error",
                    f"Error adding log to profile ID {profile_id}: {e}",
                    dialog_type="error",
                )
                logging.error(
                    f"OCL API error adding log to profile ID {profile_id}: {e}",
                    exc_info=True,
                )

            if self.status_bar:
                self.status_bar.configure(
                    text=f"Add Log to OCL profile ID {profile_id} (Type: {log_type_lower}). Success: {success}"
                )
        else:  # This 'else' corresponds to 'if log_text_to_add is not None:'
            # This case should ideally be caught earlier, e.g. if a note was cancelled.
            logging.warning(
                f"Add Log: log_text_to_add was None for profile ID {profile_id}, type {log_type_lower}. This might indicate an issue in dialog flow."
            )
            if self.status_bar:
                self.status_bar.configure(
                    text=f"Add Log: No log data to add for profile {profile_id}."
                )

    def on_ocl_profile_select_ctktable(self, selection_data):
        selected_data_row_index = selection_data.get("row")
        if selected_data_row_index is None:  # No row selected or invalid selection_data
            logging.debug(
                "on_ocl_profile_select_ctktable: No row index in selection_data."
            )
            return

        profile_id_val_str = None  # Initialize to ensure it's always bound
        selected_row_values = None  # Initialize to ensure it's always bound

        # The CTkTable returns the visual row index (0-based for data rows).
        # The header is not counted in this index if `header=True` was used or values start with header.
        # Assuming the first row in `self.ocl_profiles_table.values` is the header.
        data_list_index = selected_data_row_index + 1

        if self.ocl_profiles_table is None or not hasattr(
            self.ocl_profiles_table, "values"
        ):
            logging.warning(
                "on_ocl_profile_select_ctktable: ocl_profiles_table is not initialized or has no values."
            )
            return

        # Check if the table is empty or only contains the header
        if len(self.ocl_profiles_table.values) <= 1:  # Only header or empty
            logging.info(
                "on_ocl_profile_select_ctktable: OCL profiles table is empty or contains only header. No data to select."
            )
            self.selected_ocl_profile_id = None
            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                self.ocl_profile_details_text.delete("0.0", tk.END)
                self.ocl_profile_details_text.insert(
                    "0.0", "No profiles available or table is empty."
                )
                self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)
            return

        if (
            data_list_index >= len(self.ocl_profiles_table.values)
            or data_list_index < 1
        ):  # data_list_index < 1 means header was clicked if 0
            logging.warning(
                f"on_ocl_profile_select_ctktable: Selection index {selected_data_row_index} (data list index {data_list_index}) is out of bounds for the data list of size {len(self.ocl_profiles_table.values)}."
            )
            return

        try:
            selected_row_values = self.ocl_profiles_table.values[data_list_index]
            profile_id_val_str = selected_row_values[
                0
            ]  # Assuming ID is the first column

            if not str(
                profile_id_val_str
            ).isdigit():  # Check if it's a placeholder like "No profiles found."
                logging.info(
                    f"on_ocl_profile_select_ctktable: Non-data row clicked. Content: '{profile_id_val_str}'"
                )
                self.selected_ocl_profile_id = None
                if self.ocl_profile_details_text:
                    self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                    self.ocl_profile_details_text.delete("0.0", tk.END)
                    self.ocl_profile_details_text.insert(
                        "0.0", "Select a valid profile to view details."
                    )
                    self.ocl_profile_details_text.configure(
                        state=customtkinter.DISABLED
                    )
                return

            self.selected_ocl_profile_id = int(profile_id_val_str)
            logging.info(
                f"OCL profile selected via CTkTable. Row index: {selected_data_row_index}, ID: {self.selected_ocl_profile_id}"
            )
            details = ocl_api.get_profile_details(self.selected_ocl_profile_id)

            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.configure(state=customtkinter.NORMAL)
                self.ocl_profile_details_text.delete("0.0", tk.END)
                if details:
                    display_text = f"Profile: {details.get('name', 'N/A')} (ID: {details.get('id')})\n"
                    display_text += (
                        f"Description: {details.get('description', 'N/A')}\n\n"
                    )

                    display_text += "Settings:\n"
                    if details.get("settings"):
                        for setting in details.get("settings", []):
                            display_text += f"  - {setting.get('category', 'N/A')} -> {setting.get('setting_name', 'N/A')}: {setting.get('setting_value', 'N/A')} (Type: {setting.get('value_type', 'str')})\n"
                    else:
                        display_text += "  (No settings for this profile)\n"

                    display_text += "\nLogs:\n"
                    if details.get("logs"):
                        for log in details.get("logs", []):
                            display_text += f"  - [{log.get('timestamp', 'N/A')}]: {log.get('log_text', 'N/A')}\n"
                    else:
                        display_text += "  (No logs for this profile)\n"

                    self.ocl_profile_details_text.insert("0.0", display_text)
                else:
                    self.ocl_profile_details_text.insert(
                        "0.0",
                        f"No details found for profile ID: {self.selected_ocl_profile_id}",
                    )
                self.ocl_profile_details_text.configure(state=customtkinter.DISABLED)
        except ValueError:
            logging.error(
                f"Error converting profile ID '{profile_id_val_str}' to int.",
                exc_info=True,
            )
            show_custom_messagebox(
                self,
                "OCL Error",
                f"Could not process profile ID: '{profile_id_val_str}'.",
                dialog_type="error",
            )
            self.selected_ocl_profile_id = None
        except IndexError:
            logging.error(
                f"Error accessing profile data at index {data_list_index}. Row content: {selected_row_values if 'selected_row_values' in locals() else 'Unknown'}",
                exc_info=True,
            )
            show_custom_messagebox(
                self,
                "OCL Error",
                "Could not retrieve all data for the selected profile row.",
                dialog_type="error",
            )
            self.selected_ocl_profile_id = None
        except Exception as e:  # Catch any other unexpected error during processing
            logging.error(
                f"Unexpected error processing OCL profile selection: {e}", exc_info=True
            )
            show_custom_messagebox(
                self,
                "OCL Error",
                f"An unexpected error occurred: {e}",
                dialog_type="error",
            )
            self.selected_ocl_profile_id = None

    def save_combined_report(self):
        dialog = CTkFileDialog(
            master=self,
            title="Select Output Directory for Reports",
            open_folder=True,
            initialdir=os.path.abspath(DEFAULT_OUTPUT_DIR),
        )
        output_dir = dialog.get()

        if not output_dir:
            show_custom_messagebox(
                self, "Cancelled", "Save report cancelled.", dialog_type="info"
            )
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
                sys_inv_data_for_report = []
            output_to_json_combined(
                sys_inv_data_for_report,
                self.devenv_components_results,
                self.devenv_env_vars_results,
                self.devenv_issues_results,
                output_dir,
            )
            output_to_markdown_combined(
                sys_inv_data_for_report,
                self.devenv_components_results,
                self.devenv_env_vars_results,
                self.devenv_issues_results,
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
                f"Error saving reports: {e}\n{traceback.format_exc()}", exc_info=True
            )
            show_custom_messagebox(
                self, "Save Error", f"Failed to save reports: {e}", dialog_type="error"
            )

    def quit_app(self):
        if self.scan_in_progress:
            # For simplicity, directly destroying. A real app might use a custom dialog for confirmation.
            # show_custom_messagebox(self, "Quit Confirmation", "A scan is currently in progress. Are you sure you want to quit?", dialog_type="warning", confirm_callback=self._quit_app_confirmed)
            # For now, let's assume the user confirms or we decide to quit anyway.
            # If a confirm_callback was implemented for show_custom_messagebox, it would handle self.destroy()
            # Since it's not, and to avoid hanging, we'll just destroy.
            logging.warning("Quitting while scan in progress (simplified handling).")
            self.destroy()
        else:
            self.destroy()

    # def _quit_app_confirmed(self): # This method was referenced but not defined.
    #     self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="System Sage - Integrated System Utility V2.0"
    )
    parser.add_argument(
        "--no-disk-usage",
        action="store_false",
        dest="calculate_disk_usage",
        default=DEFAULT_CALCULATE_DISK_USAGE,
        help="Disable disk usage calculation for System Inventory.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Default directory for output files (default: {DEFAULT_OUTPUT_DIR}).",
    )
    markdown_components_group = parser.add_mutually_exclusive_group()
    markdown_components_group.add_argument(
        "--md-include-components",
        action="store_true",
        dest="markdown_include_components_flag",
        default=None,
        help="Include components/drivers in Markdown report.",
    )
    markdown_components_group.add_argument(
        "--md-no-components",
        action="store_false",
        dest="markdown_include_components_flag",
        default=None,
        help="Exclude components/drivers from Markdown report.",
    )
    args = parser.parse_args()
    if args.markdown_include_components_flag is None:
        args.markdown_include_components_flag = DEFAULT_MARKDOWN_INCLUDE_COMPONENTS
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s [%(levelname)s] - %(threadName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    try:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    except Exception as e:
        logging.error(
            f"Error creating default output directory '{DEFAULT_OUTPUT_DIR}': {e}",
            exc_info=True,
        )

    try:
        ocl_db_path = resource_path(
            os.path.join("ocl_module_src", "system_sage_olb.db")
        )
        os.makedirs(os.path.dirname(ocl_db_path), exist_ok=True)
        logging.info(
            f"OCL DB expected at: {ocl_db_path} (actual path handled by ocl_module)"
        )
    except Exception as e:
        logging.error(f"Error preparing OCL DB path: {e}", exc_info=True)

    try:
        app = SystemSageApp(cli_args=args)
        app.mainloop()
    except Exception as e:
        logging.critical("GUI Crashed: %s", e, exc_info=True)
        try:
            from tkinter import messagebox

            root_err = tk.Tk()
            root_err.withdraw()
            messagebox.showerror("Fatal GUI Error", f"A critical error occurred: {e}")
            root_err.destroy()
        except Exception as critical_e:
            print(f"CRITICAL FALLBACK ERROR: {critical_e}", file=sys.stderr)
            print(f"Original critical error: {e}", file=sys.stderr)
