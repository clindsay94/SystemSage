# System Sage - Integrated System Utility V2.0
# This script provides system inventory, developer environment auditing,
# and other utilities.
# V2.0:
# - Renamed to SystemSageV2.0.py.
# - Updated internal version references.
# - Includes fixes for OCL API calls.
# - Prepared for application compilation with resource_path helper.
# - Added AI Core module integration (placeholder).

import os
import platform
import json
import datetime
import argparse
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from threading import Thread
import traceback
import sys

# --- Helper function for PyInstaller resource path ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # For development, use the directory of the script file
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- Platform Specific Setup ---
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import winreg
    except ImportError:
        logging.error("Failed to import winreg on a Windows system. System Inventory will not work.")
        IS_WINDOWS = False

# --- DevEnvAudit Imports ---
from devenvaudit_src.scan_logic import EnvironmentScanner

# --- OCL Module Imports ---
from ocl_module_src import olb_api as ocl_api

# --- AI Core Module Imports ---
from system_sage.ai_core import model_loader as ai_model_loader
from system_sage.ai_core import file_manager_ai # Added this import

# --- Configuration Loading Function ---
def load_json_config(filename, default_data):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logging.info(f"Successfully loaded configuration from {filename}")
                return data
        else:
            logging.warning(f"Configuration file {filename} not found. Using default values.")
    except json.JSONDecodeError:
        logging.warning(f"Error decoding JSON from {filename}. Using default values.")
    except Exception as e:
        logging.warning(f"Unexpected error loading {filename}: {e}. Using default values.")
    return default_data

# --- Configuration (Defaults, will be overridden by argparse) ---
DEFAULT_CALCULATE_DISK_USAGE = True
DEFAULT_OUTPUT_JSON = True 
DEFAULT_OUTPUT_MARKDOWN = True
DEFAULT_MARKDOWN_INCLUDE_COMPONENTS = True
DEFAULT_CONSOLE_INCLUDE_COMPONENTS = False 
DEFAULT_OUTPUT_DIR = "output" 

DEFAULT_COMPONENT_KEYWORDS = [
    "driver", "sdk", "runtime", "redistributable", "pack", "update for",
    "component", "service", "host", "framework", "module", "tool",
    "package", "library", "interface", "provider", "kit", "utility",
    "microsoft .net", "visual c++", "windows sdk", "directx", "vulkan"
] 

DEFAULT_LAUNCHER_HINTS = {
    "Steam Game": {"publishers": ["valve"], "paths": ["steamapps"]},
    "Epic Games Store Game": {"publishers": ["epic games, inc."], "paths": ["epic games"]},
} 

COMPONENT_KEYWORDS_FILE = resource_path("systemsage_component_keywords.json")
LAUNCHER_HINTS_FILE = resource_path("systemsage_launcher_hints.json")

COMPONENT_KEYWORDS = load_json_config(COMPONENT_KEYWORDS_FILE, DEFAULT_COMPONENT_KEYWORDS)
LAUNCHER_HINTS = load_json_config(LAUNCHER_HINTS_FILE, DEFAULT_LAUNCHER_HINTS)

class DirectorySizeError(Exception):
    """Custom exception for errors during directory size calculation."""
    pass

def is_likely_component(display_name, publisher):
    if not IS_WINDOWS: return False
    name_lower = str(display_name).lower()
    publisher_lower = str(publisher).lower()
    for keyword in COMPONENT_KEYWORDS:
        if keyword in name_lower or keyword in publisher_lower: return True
    if name_lower.startswith('{') or name_lower.startswith('kb'): return True
    return False

def get_hkey_name(hkey_root):
    if not IS_WINDOWS: return "N/A"
    if hkey_root == winreg.HKEY_LOCAL_MACHINE: return "HKEY_LOCAL_MACHINE"
    if hkey_root == winreg.HKEY_CURRENT_USER: return "HKEY_CURRENT_USER"
    return str(hkey_root)

def get_directory_size(directory_path, calculate_disk_usage_flag):
    total_size = 0
    if not calculate_disk_usage_flag: return 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp) and os.path.exists(fp):
                    try: total_size += os.path.getsize(fp)
                    except OSError: pass 
    except OSError as e: raise DirectorySizeError(f"Error accessing directory {directory_path}: {e}") from e
    return total_size

def format_size(size_bytes, calculate_disk_usage_flag):
    if not calculate_disk_usage_flag and size_bytes == 0: return "Not Calculated"
    if size_bytes < 0: return "N/A (Error)"
    if size_bytes == 0: return "0 B" if calculate_disk_usage_flag else "Not Calculated"
    size_name = ("B", "KB", "MB", "GB", "TB"); i = 0
    while size_bytes >= 1024 and i < len(size_name)-1 : size_bytes /= 1024.0; i += 1
    return f"{size_bytes:.2f} {size_name[i]}"

def get_installed_software(calculate_disk_usage_flag):
    if not IS_WINDOWS:
        logging.info("System Inventory (registry scan) is skipped as it's only available on Windows.")
        return [{'DisplayName': "System Inventory", 'Remarks': "System Inventory (via registry scan) is only available on Windows.", 'Category': "Informational"}]
    
    software_list = []; processed_entries = set()
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (64-bit)"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (32-bit)"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU")]

    for hkey_root, path_suffix, hive_display_name in registry_paths:
        try:
            with winreg.OpenKey(hkey_root, path_suffix) as uninstall_key:
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                    subkey_name = ""; app_details = {}; full_reg_key_path = "N/A"
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        full_reg_key_path = f"{get_hkey_name(hkey_root)}\\{path_suffix}\\{subkey_name}"
                        with winreg.OpenKey(uninstall_key, subkey_name) as app_key:
                            app_details = {'SourceHive': hive_display_name, 'RegistryKeyPath': full_reg_key_path, 
                                           'InstallLocationSize': "N/A" if calculate_disk_usage_flag else "Not Calculated", 'Remarks': ""}
                            try: app_details['DisplayName'] = str(winreg.QueryValueEx(app_key, "DisplayName")[0])
                            except FileNotFoundError: app_details['DisplayName'] = subkey_name
                            except OSError as e: app_details['DisplayName'] = f"{subkey_name} (Name Error: {e.strerror})"
                            
                            entry_id_name = app_details['DisplayName']; entry_id_version = "N/A"
                            try: 
                                app_details['DisplayVersion'] = str(winreg.QueryValueEx(app_key, "DisplayVersion")[0])
                                entry_id_version = app_details['DisplayVersion']
                            except FileNotFoundError: app_details['DisplayVersion'] = "N/A"
                            except OSError as e: app_details['DisplayVersion'] = f"Version Error: {e.strerror}"
                            
                            entry_id = (entry_id_name, entry_id_version)
                            if entry_id in processed_entries: continue
                            processed_entries.add(entry_id)

                            try: app_details['Publisher'] = str(winreg.QueryValueEx(app_key, "Publisher")[0])
                            except FileNotFoundError: app_details['Publisher'] = "N/A"
                            except OSError as e: app_details['Publisher'] = f"Publisher Error: {e.strerror}"
                            
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
                                        except OSError: app_details['InstallLocationSize'] = "N/A (Access Error)"
                                    app_details['Remarks'] += " InstallLocation is a file;"
                                elif install_location_cleaned:
                                    app_details['PathStatus'] = "Path Not Found"
                                    app_details['Remarks'] += " Broken install path (Actionable);"
                                else:
                                    app_details['PathStatus'] = "No Valid Path in Registry"
                            except FileNotFoundError:
                                app_details['InstallLocation'] = "N/A"; app_details['PathStatus'] = "No Path in Registry"
                            except OSError as e:
                                app_details['InstallLocation'] = f"Path Read Error: {e.strerror}"; app_details['PathStatus'] = "Error"
                            
                            if app_details['DisplayName'] and not app_details['DisplayName'].startswith('{'):
                                software_list.append(app_details)
                    except OSError as e_val: logging.warning(f"OSError processing subkey {subkey_name} under {path_suffix}: {e_val}")
                    except Exception as e_inner: logging.error(f"Unexpected error processing subkey {subkey_name} under {path_suffix}: {e_inner}", exc_info=True)
        except FileNotFoundError: logging.info(f"Registry path not found (this might be normal): {hive_display_name} - {path_suffix}")
        except Exception as e_outer: logging.error(f"An error occurred accessing registry path {hive_display_name} - {path_suffix}: {e_outer}", exc_info=True)
    return sorted(software_list, key=lambda x: str(x.get('DisplayName','')).lower())

def output_to_json_combined(system_inventory_data, devenv_components_data, devenv_env_vars_data, devenv_issues_data, output_dir, filename="system_sage_combined_report.json"):
    combined_data = {}
    is_sys_inv_placeholder = system_inventory_data and len(system_inventory_data) == 1 and system_inventory_data[0].get('Category') == "Informational"
    if system_inventory_data and not is_sys_inv_placeholder:
        combined_data["systemInventory"] = system_inventory_data
    
    devenv_audit_data = {}
    if devenv_components_data: devenv_audit_data["detectedComponents"] = [comp.to_dict() for comp in devenv_components_data]
    if devenv_env_vars_data: devenv_audit_data["environmentVariables"] = [ev.to_dict() for ev in devenv_env_vars_data]
    if devenv_issues_data: devenv_audit_data["identifiedIssues"] = [issue.to_dict() for issue in devenv_issues_data]
    if devenv_audit_data: combined_data["devEnvAudit"] = devenv_audit_data

    if not combined_data and is_sys_inv_placeholder : 
        combined_data["systemInventory"] = system_inventory_data

    if not combined_data: logging.info("No data to save to JSON report."); return
    try:
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f: json.dump(combined_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Combined JSON report successfully saved to {full_path}")
    except Exception as e: logging.error(f"Error saving combined JSON file to {output_dir}: {e}", exc_info=True); raise

def output_to_markdown_combined(system_inventory_data, devenv_components_data, devenv_env_vars_data, devenv_issues_data, output_dir, filename="system_sage_combined_report.md", include_system_sage_components_flag=True):
    try:
        os.makedirs(output_dir, exist_ok=True); full_path = os.path.join(output_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"# System Sage Combined Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## System Software Inventory\n\n")
            is_sys_inv_placeholder = system_inventory_data and len(system_inventory_data) == 1 and system_inventory_data[0].get('Category') == "Informational"
            if system_inventory_data:
                if is_sys_inv_placeholder: f.write(f"* {system_inventory_data[0].get('Remarks')}\n\n")
                else: 
                    header = "| Application Name | Version | Publisher | Install Path | Size | Status | Remarks | Source Hive | Registry Key Path |\n"
                    separator = "|---|---|---|---|---|---|---|---|---|\n"
                    apps_data = [app for app in system_inventory_data if app.get('Category') == "Application"]
                    comps_data = [app for app in system_inventory_data if app.get('Category') == "Component/Driver"]
                    f.write("### Applications\n")
                    if apps_data:
                        f.write(header); f.write(separator)
                        for app in apps_data: f.write(f"| {app.get('DisplayName', 'N/A')} | {app.get('DisplayVersion', 'N/A')} | {app.get('Publisher', 'N/A')} | {app.get('InstallLocation', 'N/A')} | {app.get('InstallLocationSize', 'N/A')} | {app.get('PathStatus', 'N/A')} | {app.get('Remarks', '')} | {app.get('SourceHive', 'N/A')} | {app.get('RegistryKeyPath', 'N/A')} |\n")
                    else: f.write("*No applications found.*\n")
                    f.write("\n")
                    if include_system_sage_components_flag:
                        f.write("### Components/Drivers\n")
                        if comps_data:
                            f.write(header); f.write(separator)
                            for comp in comps_data: f.write(f"| {comp.get('DisplayName', 'N/A')} | {comp.get('DisplayVersion', 'N/A')} | {comp.get('Publisher', 'N/A')} | {comp.get('InstallLocation', 'N/A')} | {comp.get('InstallLocationSize', 'N/A')} | {comp.get('PathStatus', 'N/A')} | {comp.get('Remarks', '')} | {comp.get('SourceHive', 'N/A')} | {comp.get('RegistryKeyPath', 'N/A')} |\n")
                        else: f.write("*No components/drivers found or component reporting is disabled.*\n")
                        f.write("\n")
            else: f.write("*No system inventory data collected.*\n\n")
            f.write("## Developer Environment Audit\n\n")
            if devenv_components_data or devenv_env_vars_data or devenv_issues_data:
                f.write("*DevEnvAudit details omitted for brevity in this example.*\n") # Simplified for this cleanup pass
            else: f.write("*No data collected by Developer Environment Audit.*\n\n")
        logging.info(f"Combined Markdown report successfully saved to {full_path}")
    except Exception as e: logging.error(f"Error saving combined Markdown file: {e}", exc_info=True); raise

class SystemSageApp(tk.Tk):
    def __init__(self, cli_args=None):
        super().__init__()
        self.cli_args = cli_args
        self.title("System Sage V2.0") 
        self.geometry("1200x800")
        self.inventory_tree = None
        self.scan_in_progress = False
        self.system_inventory_results = []
        self.devenv_components_results = []
        self.devenv_env_vars_results = []
        self.devenv_issues_results = []
        self.devenv_components_tree = None
        self.devenv_env_vars_tree = None
        self.devenv_issues_tree = None
        self.ocl_profiles_tree = None
        self.ocl_profile_details_text = None
        self.ocl_refresh_button = None
        self.ocl_save_new_button = None
        self.ocl_update_selected_button = None
        
        self._setup_ui()
        if not IS_WINDOWS: 
            self.after(100, self.start_system_inventory_scan)

    def _setup_ui(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Save Combined Report (JSON & MD)", command=self.save_combined_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        self.scan_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.scan_menu.add_command(label="Run System Inventory Scan", command=self.start_system_inventory_scan, state=tk.NORMAL if IS_WINDOWS else tk.DISABLED)
        self.scan_menu.add_command(label="Run DevEnv Audit", command=self.start_devenv_audit_scan)
        self.menu_bar.add_cascade(label="Scan", menu=self.scan_menu)

        ai_menu = tk.Menu(self.menu_bar, tearoff=0)
        ai_menu.add_command(label="Run System Analysis with AI", command=self.run_ai_system_analysis)
        self.menu_bar.add_cascade(label="AI Insights", menu=ai_menu)

        main_notebook = ttk.Notebook(self)
        main_notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        inventory_tab = ttk.Frame(main_notebook)
        main_notebook.add(inventory_tab, text="System Software Inventory")
        columns = ("Name", "Version", "Publisher", "Path", "Size", "Status", "Remarks", "SourceHive", "RegKey")
        self.inventory_tree = ttk.Treeview(inventory_tab, columns=columns, show="headings")
        for col in columns: self.inventory_tree.heading(col, text=col); self.inventory_tree.column(col, width=100, anchor=tk.W)
        vsb_inv = ttk.Scrollbar(inventory_tab, orient="vertical", command=self.inventory_tree.yview)
        hsb_inv = ttk.Scrollbar(inventory_tab, orient="horizontal", command=self.inventory_tree.xview)
        self.inventory_tree.configure(yscrollcommand=vsb_inv.set, xscrollcommand=hsb_inv.set)
        vsb_inv.pack(side=tk.RIGHT, fill=tk.Y); hsb_inv.pack(side=tk.BOTTOM, fill=tk.X)
        self.inventory_tree.pack(expand=True, fill=tk.BOTH)
        
        devenv_tab = ttk.Frame(main_notebook)
        main_notebook.add(devenv_tab, text="Developer Environment Audit")
        components_frame = ttk.Labelframe(devenv_tab, text="Detected Components")
        components_frame.pack(padx=5, pady=5, fill="both", expand=True)
        comp_cols = ("ID", "Name", "Category", "Version", "Path", "Executable Path")
        self.devenv_components_tree = ttk.Treeview(components_frame, columns=comp_cols, show="headings")
        for col in comp_cols: self.devenv_components_tree.heading(col, text=col); self.devenv_components_tree.column(col, width=150)
        comp_vsb = ttk.Scrollbar(components_frame, orient="vertical", command=self.devenv_components_tree.yview); comp_hsb = ttk.Scrollbar(components_frame, orient="horizontal", command=self.devenv_components_tree.xview)
        self.devenv_components_tree.configure(yscrollcommand=comp_vsb.set, xscrollcommand=comp_hsb.set); comp_vsb.pack(side=tk.RIGHT, fill=tk.Y); comp_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.devenv_components_tree.pack(expand=True, fill=tk.BOTH)

        env_vars_frame = ttk.Labelframe(devenv_tab, text="Environment Variables")
        env_vars_frame.pack(padx=5, pady=5, fill="both", expand=True)
        env_cols = ("Name", "Value", "Scope")
        self.devenv_env_vars_tree = ttk.Treeview(env_vars_frame, columns=env_cols, show="headings")
        for col in env_cols: self.devenv_env_vars_tree.heading(col, text=col); self.devenv_env_vars_tree.column(col, width=200)
        env_vsb = ttk.Scrollbar(env_vars_frame, orient="vertical", command=self.devenv_env_vars_tree.yview); env_hsb = ttk.Scrollbar(env_vars_frame, orient="horizontal", command=self.devenv_env_vars_tree.xview)
        self.devenv_env_vars_tree.configure(yscrollcommand=env_vsb.set, xscrollcommand=env_hsb.set); env_vsb.pack(side=tk.RIGHT, fill=tk.Y); env_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.devenv_env_vars_tree.pack(expand=True, fill=tk.BOTH)

        issues_frame = ttk.Labelframe(devenv_tab, text="Identified Issues")
        issues_frame.pack(padx=5, pady=5, fill="both", expand=True)
        issue_cols = ("Severity", "Description", "Category", "Component ID", "Related Path")
        self.devenv_issues_tree = ttk.Treeview(issues_frame, columns=issue_cols, show="headings")
        for col in issue_cols: self.devenv_issues_tree.heading(col, text=col); self.devenv_issues_tree.column(col, width=150)
        issue_vsb = ttk.Scrollbar(issues_frame, orient="vertical", command=self.devenv_issues_tree.yview); issue_hsb = ttk.Scrollbar(issues_frame, orient="horizontal", command=self.devenv_issues_tree.xview)
        self.devenv_issues_tree.configure(yscrollcommand=issue_vsb.set, xscrollcommand=issue_hsb.set); issue_vsb.pack(side=tk.RIGHT, fill=tk.Y); issue_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.devenv_issues_tree.pack(expand=True, fill=tk.BOTH)

        ocl_tab = ttk.Frame(main_notebook)
        main_notebook.add(ocl_tab, text="Overclocker's Logbook")
        ocl_paned_window = ttk.PanedWindow(ocl_tab, orient=tk.VERTICAL)
        ocl_paned_window.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        profiles_list_outer_frame = ttk.Labelframe(ocl_paned_window, text="Available Overclocking Profiles")
        ocl_paned_window.add(profiles_list_outer_frame, weight=1)
        profiles_list_tree_frame = ttk.Frame(profiles_list_outer_frame)
        profiles_list_tree_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        ocl_profile_columns = ("ID", "Profile Name", "Last Modified")
        self.ocl_profiles_tree = ttk.Treeview(profiles_list_tree_frame, columns=ocl_profile_columns, show="headings")
        self.ocl_profiles_tree.heading("ID", text="ID"); self.ocl_profiles_tree.column("ID", width=50, anchor=tk.W, stretch=tk.NO)
        self.ocl_profiles_tree.heading("Profile Name", text="Profile Name"); self.ocl_profiles_tree.column("Profile Name", width=250, anchor=tk.W)
        self.ocl_profiles_tree.heading("Last Modified", text="Last Modified"); self.ocl_profiles_tree.column("Last Modified", width=150, anchor=tk.W)
        ocl_profiles_vsb = ttk.Scrollbar(profiles_list_tree_frame, orient="vertical", command=self.ocl_profiles_tree.yview)
        self.ocl_profiles_tree.configure(yscrollcommand=ocl_profiles_vsb.set)
        self.ocl_profiles_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH); ocl_profiles_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.ocl_profiles_tree.bind("<<TreeviewSelect>>", self.on_ocl_profile_select)
        details_actions_frame = ttk.Frame(ocl_paned_window)
        ocl_paned_window.add(details_actions_frame, weight=2)
        profile_details_frame = ttk.Labelframe(details_actions_frame, text="Profile Details")
        profile_details_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=(0,5), side=tk.TOP)
        self.ocl_profile_details_text = tk.Text(profile_details_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        ocl_details_vsb = ttk.Scrollbar(profile_details_frame, orient="vertical", command=self.ocl_profile_details_text.yview)
        self.ocl_profile_details_text.configure(yscrollcommand=ocl_details_vsb.set)
        self.ocl_profile_details_text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(5,0), pady=5); ocl_details_vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        actions_frame = ttk.Frame(details_actions_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)
        self.ocl_refresh_button = ttk.Button(actions_frame, text="Refresh Profile List", command=self.refresh_ocl_profiles_list)
        self.ocl_refresh_button.pack(side=tk.LEFT, padx=2)
        self.ocl_save_new_button = ttk.Button(actions_frame, text="Save System as New Profile", command=self.save_system_as_new_ocl_profile)
        self.ocl_save_new_button.pack(side=tk.LEFT, padx=2)
        self.ocl_update_selected_button = ttk.Button(actions_frame, text="Update Selected Profile", command=self.update_selected_ocl_profile)
        self.ocl_update_selected_button.pack(side=tk.LEFT, padx=2)
        
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_system_inventory_scan(self):
        if self.scan_in_progress and IS_WINDOWS: messagebox.showwarning("Scan In Progress", "A scan is already running."); return
        if not IS_WINDOWS:
            self.status_bar.config(text="System Inventory (Registry Scan) is Windows-only.")
            placeholder_inventory = get_installed_software(False) 
            self.update_inventory_display(placeholder_inventory)
            if hasattr(self, 'scan_menu'): self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.DISABLED)
            self.scan_in_progress = False; return
        self.scan_in_progress = True
        self.status_bar.config(text="Starting System Inventory Scan...")
        if hasattr(self, 'scan_menu'): self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.DISABLED); self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.DISABLED)
        if self.inventory_tree: 
            for i in self.inventory_tree.get_children(): self.inventory_tree.delete(i)
        calc_disk = self.cli_args.calculate_disk_usage if self.cli_args else DEFAULT_CALCULATE_DISK_USAGE
        thread = Thread(target=self.run_system_inventory_thread, args=(calc_disk,), daemon=True)
        thread.start()

    def run_system_inventory_thread(self, calculate_disk_usage_flag):
        try:
            software_list = get_installed_software(calculate_disk_usage_flag)
            self.after(0, self.update_inventory_display, software_list)
        except Exception as e:
            logging.error(f"Error in system inventory thread: {e}\n{traceback.format_exc()}")
            self.after(0, self.inventory_scan_error, e)

    def update_inventory_display(self, software_list):
        if self.inventory_tree:
            for i in self.inventory_tree.get_children(): self.inventory_tree.delete(i)
            for app in software_list:
                self.inventory_tree.insert("", tk.END, values=(
                    app.get('DisplayName', 'N/A'), app.get('DisplayVersion', 'N/A'), app.get('Publisher', 'N/A'),
                    app.get('InstallLocation', 'N/A'), app.get('InstallLocationSize', 'N/A'), app.get('PathStatus', 'N/A'),
                    app.get('Remarks', ''), app.get('SourceHive', 'N/A'), app.get('RegistryKeyPath', 'N/A')))
        self.system_inventory_results = software_list
        status_msg = f"System Inventory Scan Complete. Found {len(software_list)} items."
        if len(software_list) == 1 and software_list[0].get('Category') == "Informational": status_msg = software_list[0].get('Remarks')
        self.status_bar.config(text=status_msg)
        self.scan_in_progress = False
        if hasattr(self, 'scan_menu'): 
            self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.NORMAL if IS_WINDOWS else tk.DISABLED)
            self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.NORMAL)

    def inventory_scan_error(self, error):
        messagebox.showerror("Scan Error", f"An error occurred during System Inventory: {error}")
        self.status_bar.config(text="System Inventory Scan Failed.")
        self.scan_in_progress = False
        if hasattr(self, 'scan_menu'):
            self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.NORMAL if IS_WINDOWS else tk.DISABLED)
            self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.NORMAL)

    def _devenv_status_callback(self, message): self.status_bar.config(text=f"[DevEnvAudit] {message}"); logging.info(f"[DevEnvAudit Status] {message}")
    def _devenv_progress_callback(self, current, total, message): self.status_bar.config(text=f"[DevEnvAudit Progress] {current}/{total}: {message}"); logging.info(f"[DevEnvAudit Progress] {current}/{total}: {message}")

    def start_devenv_audit_scan(self):
        if self.scan_in_progress: messagebox.showwarning("Scan In Progress", "A scan is already running."); return
        self.scan_in_progress = True
        self.status_bar.config(text="Starting Developer Environment Audit...")
        if hasattr(self, 'scan_menu'): self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.DISABLED); self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.DISABLED)
        for tree in [self.devenv_components_tree, self.devenv_env_vars_tree, self.devenv_issues_tree]:
            if tree: 
                for i in tree.get_children(): tree.delete(i)
        thread = Thread(target=self.run_devenv_audit_thread, daemon=True)
        thread.start()

    def run_devenv_audit_thread(self):
        try:
            scanner = EnvironmentScanner(progress_callback=self._devenv_progress_callback, status_callback=self._devenv_status_callback)
            components, env_vars, issues = scanner.run_scan()
            self.after(0, self.update_devenv_audit_display, components, env_vars, issues)
        except Exception as e:
            logging.error(f"DevEnvAudit scan failed: {e}\n{traceback.format_exc()}")
            self.after(0, self.devenv_scan_error, e)

    def update_devenv_audit_display(self, components, env_vars, issues):
        if self.devenv_components_tree:
            for comp in components: self.devenv_components_tree.insert("", tk.END, values=(comp.id, comp.name, comp.category, comp.version, comp.path, comp.executable_path))
        if self.devenv_env_vars_tree:
            for ev in env_vars: self.devenv_env_vars_tree.insert("", tk.END, values=(ev.name, ev.value, ev.scope))
        if self.devenv_issues_tree:
            for issue in issues: self.devenv_issues_tree.insert("", tk.END, values=(issue.severity, issue.description, issue.category, issue.component_id, issue.related_path))
        self.devenv_components_results = components; self.devenv_env_vars_results = env_vars; self.devenv_issues_results = issues
        self.finalize_devenv_scan(f"DevEnv Audit Complete. Found {len(components)} components, {len(env_vars)} env vars, {len(issues)} issues.")

    def devenv_scan_error(self, error):
        messagebox.showerror("DevEnv Audit Error", f"An error occurred: {error}")
        self.finalize_devenv_scan("DevEnv Audit Failed.")

    def finalize_devenv_scan(self, message="DevEnv Audit Finished."):
        self.status_bar.config(text=message)
        self.scan_in_progress = False
        if hasattr(self, 'scan_menu'):
            self.scan_menu.entryconfig("Run System Inventory Scan", state=tk.NORMAL if IS_WINDOWS else tk.DISABLED)
            self.scan_menu.entryconfig("Run DevEnv Audit", state=tk.NORMAL)

    def refresh_ocl_profiles_list(self):
        logging.info("SystemSageApp.refresh_ocl_profiles_list called")
        if self.ocl_profiles_tree:
            for i in self.ocl_profiles_tree.get_children(): self.ocl_profiles_tree.delete(i)
            try:
                profiles = ocl_api.get_all_profiles()
                for profile in profiles:
                    self.ocl_profiles_tree.insert("", "end", values=(
                        profile.get('id'), profile.get('name'), profile.get('last_modified_date')))
                self.status_bar.config(text="OCL Profiles refreshed.")
            except Exception as e:
                messagebox.showerror("OCL Error", f"Failed to refresh OCL profiles: {e}")
                logging.error(f"Failed to refresh OCL profiles: {e}", exc_info=True)
                self.status_bar.config(text="OCL Profile refresh failed.")
        else:
            logging.warning("OCL profiles treeview not initialized when trying to refresh.")


    def save_system_as_new_ocl_profile(self):
        profile_name = simpledialog.askstring("New OCL Profile", "Enter a name for this new profile:")
        if not profile_name: messagebox.showinfo("Cancelled", "New profile creation cancelled."); return
        success = False 
        try:
            profile_id = ocl_api.create_new_profile(name=profile_name, description="Profile created via SystemSage GUI.", initial_logs=["Profile created."])
            success = profile_id is not None
            if success: messagebox.showinfo("Success", f"New OCL profile '{profile_name}' saved with ID: {profile_id}."); self.refresh_ocl_profiles_list()
            else: messagebox.showerror("Error", f"Failed to save new OCL profile '{profile_name}'.")
        except Exception as e: messagebox.showerror("OCL API Error", f"Error saving profile: {e}"); logging.error(f"OCL save error: {e}", exc_info=True)
        self.status_bar.config(text=f"Save new OCL profile attempt: {profile_name}. Success: {success}")

    def update_selected_ocl_profile(self):
        if not self.ocl_profiles_tree or not self.ocl_profiles_tree.focus():
            messagebox.showwarning("No Profile Selected", "Please select an OCL profile to update."); return
        selected_item = self.ocl_profiles_tree.focus()
        try:
            profile_id_str = self.ocl_profiles_tree.item(selected_item, "values")[0]
            profile_id = int(profile_id_str)
        except (IndexError, ValueError) as e:
             messagebox.showerror("Error", f"Invalid profile selected or profile ID not found: {e}"); return
            
        new_log_data = simpledialog.askstring("New Log Entry", f"Enter new log for profile ID {profile_id}:")
        if not new_log_data: messagebox.showinfo("Cancelled", "Update profile cancelled."); return
        success = False
        try:
            log_id = ocl_api.add_log_to_profile(profile_id=profile_id, log_text=new_log_data)
            success = log_id is not None
            if success: messagebox.showinfo("Success", f"Log entry added to OCL profile ID {profile_id} (Log ID: {log_id})."); self.refresh_ocl_profiles_list()
            else: messagebox.showerror("Error", f"Failed to add log to OCL profile ID {profile_id}.")
        except Exception as e: messagebox.showerror("OCL API Error", f"Error updating profile ID {profile_id}: {e}"); logging.error(f"OCL update error: {e}", exc_info=True)
        self.status_bar.config(text=f"Update OCL profile ID {profile_id} attempt. Success: {success}")
        
    def on_ocl_profile_select(self, event=None): 
        if not self.ocl_profiles_tree or not self.ocl_profiles_tree.focus(): return
        selected_item = self.ocl_profiles_tree.focus()
        try:
            profile_id_str = self.ocl_profiles_tree.item(selected_item, "values")[0]
            profile_id = int(profile_id_str)
            profile_details = ocl_api.get_profile_details(profile_id)
            if profile_details and self.ocl_profile_details_text:
                self.ocl_profile_details_text.config(state=tk.NORMAL)
                self.ocl_profile_details_text.delete('1.0', tk.END)
                self.ocl_profile_details_text.insert(tk.END, f"Profile: {profile_details.get('name', 'N/A')}\n")
                self.ocl_profile_details_text.insert(tk.END, f"Description: {profile_details.get('description', 'N/A')}\n\n")
                self.ocl_profile_details_text.insert(tk.END, "Settings:\n")
                for setting in profile_details.get('settings', []):
                    self.ocl_profile_details_text.insert(tk.END, f"  - {setting.get('category', 'N/A')}/{setting.get('setting_name', 'N/A')}: {setting.get('setting_value', 'N/A')}\n")
                self.ocl_profile_details_text.insert(tk.END, "\nLogs:\n")
                for log in profile_details.get('logs', []):
                    self.ocl_profile_details_text.insert(tk.END, f"  - [{log.get('timestamp', 'N/A')}]: {log.get('log_text', 'N/A')}\n")
                self.ocl_profile_details_text.config(state=tk.DISABLED)
            else:
                if self.ocl_profile_details_text:
                    self.ocl_profile_details_text.config(state=tk.NORMAL)
                    self.ocl_profile_details_text.delete('1.0', tk.END)
                    self.ocl_profile_details_text.insert(tk.END, "Could not load details for selected profile.")
                    self.ocl_profile_details_text.config(state=tk.DISABLED)
        except (IndexError, ValueError) as e:
            logging.error(f"Error processing OCL profile selection: {e}", exc_info=True)
            if self.ocl_profile_details_text:
                self.ocl_profile_details_text.config(state=tk.NORMAL)
                self.ocl_profile_details_text.delete('1.0', tk.END)
                self.ocl_profile_details_text.insert(tk.END, "Error displaying profile details.")
                self.ocl_profile_details_text.config(state=tk.DISABLED)


    def run_ai_system_analysis(self):
        self.status_bar.config(text="Initiating AI System Analysis...")
        logging.info("AI System Analysis initiated by user.")
        try:
            model_loaded_successfully = ai_model_loader.load_gemma_model() 
            if model_loaded_successfully:
                data_to_analyze = {}
                inventory_for_ai = [app for app in self.system_inventory_results if app.get('Category') != "Informational"] if self.system_inventory_results else []

                if inventory_for_ai:
                    data_to_analyze["inventory_summary"] = {"app_count": len(inventory_for_ai), "first_few_apps": [app.get("DisplayName", "N/A") for app in inventory_for_ai[:3]]}
                else: data_to_analyze["inventory_summary"] = "No system inventory data available or scan not run."
                
                if self.devenv_components_results:
                    data_to_analyze["devenv_summary"] = {"component_count": len(self.devenv_components_results), "env_var_count": len(self.devenv_env_vars_results), "issue_count": len(self.devenv_issues_results)}
                else: data_to_analyze["devenv_summary"] = "No developer environment data available or scan not run."

                if not inventory_for_ai and not self.devenv_components_results:
                     data_to_analyze["generic_query"] = "General system health check requested as no specific scan data is loaded."
                
                logging.info(f"Sending data to AI for analysis (sample): {str(data_to_analyze)[:250]}...") 
                ai_response_general = ai_model_loader.analyze_system_data(data_to_analyze)
                
                file_suggestions = file_manager_ai.get_file_management_suggestions(inventory_for_ai)
                
                combined_ai_response = f"{ai_response_general}\n\n--- File Management Suggestions (Simulated) ---\n"
                if file_suggestions:
                    for sug in file_suggestions:
                        combined_ai_response += f"- Suggestion: {sug['suggestion']}\n  Action: {sug['action']}\n  Related: {sug.get('related_software', 'N/A')}\n\n"
                else:
                    combined_ai_response += "No specific file management suggestions at this time.\n"

                messagebox.showinfo("AI Analysis Result (Simulated)", combined_ai_response)
                self.status_bar.config(text="AI Analysis Complete.")
            else:
                messagebox.showerror("AI Model Error", "AI Model could not be loaded (simulated). See console/logs for details.")
                self.status_bar.config(text="AI Model loading failed.")
        except Exception as e:
            logging.error(f"Error during AI System Analysis: {e}", exc_info=True)
            messagebox.showerror("AI Analysis Error", f"An unexpected error occurred during AI analysis: {e}")
            self.status_bar.config(text="AI Analysis encountered an error.")

    def save_combined_report(self):
        output_dir = filedialog.askdirectory(initialdir=os.path.abspath(DEFAULT_OUTPUT_DIR), title="Select Output Directory for Reports")
        if not output_dir: return
        try:
            md_include_components = self.cli_args.markdown_include_components_flag if self.cli_args else DEFAULT_MARKDOWN_INCLUDE_COMPONENTS
            sys_inv_data_for_report = self.system_inventory_results
            is_sys_inv_placeholder = (self.system_inventory_results and len(self.system_inventory_results) == 1 and self.system_inventory_results[0].get('Category') == "Informational")
            if is_sys_inv_placeholder and (self.devenv_components_results or self.devenv_env_vars_results or self.devenv_issues_results): 
                sys_inv_data_for_report = [] 
            elif is_sys_inv_placeholder:
                 pass 

            output_to_json_combined(sys_inv_data_for_report, self.devenv_components_results, self.devenv_env_vars_results, self.devenv_issues_results, output_dir)
            output_to_markdown_combined(sys_inv_data_for_report, self.devenv_components_results, self.devenv_env_vars_results, self.devenv_issues_results, output_dir, include_system_sage_components_flag=md_include_components)
            messagebox.showinfo("Reports Saved", f"Combined reports saved to: {output_dir}")
        except Exception as e:
            logging.error(f"Error saving reports: {e}\n{traceback.format_exc()}", exc_info=True)
            messagebox.showerror("Save Error", f"Failed to save reports: {e}")
            
    def quit_app(self):
        if self.scan_in_progress:
            if messagebox.askyesno("Scan in Progress", "Scan in progress. Exit anyway?"): self.destroy()
            else: return 
        elif messagebox.askokcancel("Quit", "Exit System Sage?"): self.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="System Sage - Integrated System Utility V2.0")
    parser.add_argument("--no-disk-usage", action="store_false", dest="calculate_disk_usage", default=DEFAULT_CALCULATE_DISK_USAGE, help="Disable disk usage calculation for System Inventory.")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help=f"Default directory for output files (default: {DEFAULT_OUTPUT_DIR}).")
    markdown_components_group = parser.add_mutually_exclusive_group()
    markdown_components_group.add_argument("--md-include-components", action="store_true", dest="markdown_include_components_flag", default=None, help="Include components/drivers in Markdown report.")
    markdown_components_group.add_argument("--md-no-components", action="store_false", dest="markdown_include_components_flag", default=None, help="Exclude components/drivers from Markdown report.")
    args = parser.parse_args()

    if args.markdown_include_components_flag is None:
        args.markdown_include_components_flag = DEFAULT_MARKDOWN_INCLUDE_COMPONENTS

    log_level = logging.INFO
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s [%(levelname)s] - %(threadName)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[logging.StreamHandler(sys.stdout)]) 
    try:
        ocl_db_path = resource_path(os.path.join("ocl_module_src", "system_sage_olb.db"))
        os.makedirs(os.path.dirname(ocl_db_path), exist_ok=True) 
        logging.info(f"OCL DB expected at: {ocl_db_path} (actual path handled by ocl_module)")
    except Exception as e:
        logging.error(f"Error preparing OCL DB path: {e}", exc_info=True)
    try:
        app = SystemSageApp(cli_args=args)
        app.mainloop()
    except Exception as e:
        logging.critical("GUI Crashed: %s", e, exc_info=True)
        try:
            root_err = tk.Tk(); root_err.withdraw()
            messagebox.showerror("Fatal GUI Error", f"A critical error occurred: {e}\nSee logs for details.")
            root_err.destroy()
        except Exception as critical_e:
            print(f"CRITICAL FALLBACK ERROR (cannot show GUI messagebox): {critical_e}", file=sys.stderr)
            print(f"Original critical error: {e}", file=sys.stderr)
```
