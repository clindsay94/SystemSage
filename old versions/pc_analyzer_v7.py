# Python Software Inventory & Path Validator v7
# This script queries the Windows Registry to list installed software,
# validates installation paths, calculates disk usage for valid paths,
# and outputs to console, JSON, and Markdown.
# V7: Added disk usage calculation for valid InstallLocation.
#     Added 'Remarks' field for additional context.

import winreg  # Module to access the Windows registry
import os      # Module for operating system dependent functionality
import json    # Module for JSON operations
import datetime # Module to get current timestamp for output files

# --- Configuration for Filtering ---
COMPONENT_KEYWORDS = [
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

def get_directory_size(directory_path):
    """Calculates the total size of a directory in bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link or not accessible
                if not os.path.islink(fp) and os.path.exists(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError: # File might be gone or inaccessible
                        pass 
    except OSError: # Directory might be gone or inaccessible
        return -1 # Indicate error or inaccessibility
    return total_size

def format_size(size_bytes):
    """Formats size in bytes to a human-readable string (KB, MB, GB)."""
    if size_bytes < 0:
        return "N/A (Access Error)"
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name)-1 :
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"


def get_installed_software():
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
                                'InstallLocationSize': "N/A", # V7: Initialize
                                'Remarks': "" # V7: Initialize
                            }
                            
                            try:
                                app_details['DisplayName'] = str(winreg.QueryValueEx(app_key, "DisplayName")[0])
                            except FileNotFoundError:
                                app_details['DisplayName'] = subkey_name 
                            except OSError:
                                app_details['DisplayName'] = f"{subkey_name} (Error reading name)"

                            entry_id_name = app_details['DisplayName']
                            entry_id_version = "N/A"

                            try:
                                app_details['DisplayVersion'] = str(winreg.QueryValueEx(app_key, "DisplayVersion")[0])
                                entry_id_version = app_details['DisplayVersion']
                            except FileNotFoundError:
                                app_details['DisplayVersion'] = "N/A"
                            except OSError:
                                app_details['DisplayVersion'] = "Error"
                            
                            entry_id = (entry_id_name, entry_id_version)
                            if entry_id in processed_entries:
                                continue 
                            processed_entries.add(entry_id)

                            try:
                                app_details['Publisher'] = str(winreg.QueryValueEx(app_key, "Publisher")[0])
                            except FileNotFoundError:
                                app_details['Publisher'] = "N/A"
                            except OSError:
                                app_details['Publisher'] = "Error"

                            try:
                                install_location_raw = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                                install_location_cleaned = str(install_location_raw) 
                                
                                if isinstance(install_location_raw, str):
                                    temp_location = install_location_raw.strip()
                                    if (temp_location.startswith('"') and temp_location.endswith('"')) or \
                                       (temp_location.startswith("'") and temp_location.endswith("'")):
                                        install_location_cleaned = temp_location[1:-1]
                                
                                app_details['InstallLocation'] = install_location_cleaned 
                                
                                if install_location_cleaned and os.path.isdir(install_location_cleaned): # Check if it's a directory
                                    app_details['PathStatus'] = "OK"
                                    dir_size = get_directory_size(install_location_cleaned) # V7: Calculate size
                                    app_details['InstallLocationSize'] = format_size(dir_size)
                                elif install_location_cleaned and os.path.isfile(install_location_cleaned): # It's a file
                                    app_details['PathStatus'] = "OK (File)"
                                    try:
                                        file_size = os.path.getsize(install_location_cleaned)
                                        app_details['InstallLocationSize'] = format_size(file_size)
                                    except OSError:
                                        app_details['InstallLocationSize'] = "N/A (Access Error)"
                                    app_details['Remarks'] = "InstallLocation is a file."
                                elif install_location_cleaned: 
                                    app_details['PathStatus'] = "Path Not Found"
                                    app_details['Remarks'] = "Broken install path."
                                else: 
                                    app_details['PathStatus'] = "No Valid Path in Registry"
                                    app_details['Remarks'] = "Registry entry only?" if app_details.get('Category') == "Application" else ""


                            except FileNotFoundError:
                                app_details['InstallLocation'] = "N/A"
                                app_details['PathStatus'] = "No Path in Registry"
                                app_details['Remarks'] = "Registry entry only?" if app_details.get('Category') == "Application" else ""
                            except OSError:
                                app_details['InstallLocation'] = "Error Reading Path"
                                app_details['PathStatus'] = "Error"
                                app_details['Remarks'] = "Error accessing install path."

                            app_details['Category'] = "Component/Driver" if is_likely_component(app_details['DisplayName'], app_details['Publisher']) else "Application"
                            
                            # Refine remarks for applications that are components but have no path
                            if app_details['Category'] == "Component/Driver" and app_details['PathStatus'] in ["No Path in Registry", "No Valid Path in Registry"]:
                                app_details['Remarks'] = "Component without specific install path."


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

def output_to_json(software_list, filename="system_sage_inventory.json"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(software_list, f, ensure_ascii=False, indent=4)
        print(f"\nInventory successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

def output_to_markdown(software_list, filename="system_sage_inventory.md", include_components=False):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# System Sage Software Inventory - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # V7: Added Size and Remarks columns
            header = "| Application Name | Version | Publisher | Install Path | Size | Status | Remarks | Source Hive | Registry Key Path |\n"
            separator = "|---|---|---|---|---|---|---|---|---|\n" # V7: Adjusted for new columns

            f.write("## Applications\n")
            f.write(header)
            f.write(separator)
            app_count = 0
            for app in software_list:
                if app.get('Category') == "Application":
                    app_count +=1
                    name = str(app.get('DisplayName', 'N/A')).replace('|', '\|') 
                    version = str(app.get('DisplayVersion', 'N/A')).replace('|', '\|')
                    publisher = str(app.get('Publisher', 'N/A')).replace('|', '\|')
                    location = str(app.get('InstallLocation', 'N/A')).replace('|', '\|') 
                    size = str(app.get('InstallLocationSize', 'N/A')).replace('|', '\|') # V7
                    status = str(app.get('PathStatus', 'N/A')).replace('|', '\|')
                    remarks = str(app.get('Remarks', '')).replace('|', '\|') # V7
                    hive = str(app.get('SourceHive', 'N/A')).replace('|', '\|')
                    reg_key = str(app.get('RegistryKeyPath', 'N/A')).replace('|', '\|') 
                    f.write(f"| {name} | {version} | {publisher} | {location} | {size} | {status} | {remarks} | {hive} | {reg_key} |\n") # V7
            if app_count == 0:
                f.write("| No primary applications found. | | | | | | | | |\n") # V7

            if include_components:
                f.write("\n## Components & Drivers\n")
                f.write(header.replace("Application Name", "Component Name")) 
                f.write(separator)
                comp_count = 0
                for app in software_list:
                    if app.get('Category') == "Component/Driver":
                        comp_count +=1
                        name = str(app.get('DisplayName', 'N/A')).replace('|', '\|')
                        version = str(app.get('DisplayVersion', 'N/A')).replace('|', '\|')
                        publisher = str(app.get('Publisher', 'N/A')).replace('|', '\|')
                        location = str(app.get('InstallLocation', 'N/A')).replace('|', '\|')
                        size = str(app.get('InstallLocationSize', 'N/A')).replace('|', '\|') # V7
                        status = str(app.get('PathStatus', 'N/A')).replace('|', '\|')
                        remarks = str(app.get('Remarks', '')).replace('|', '\|') # V7
                        hive = str(app.get('SourceHive', 'N/A')).replace('|', '\|')
                        reg_key = str(app.get('RegistryKeyPath', 'N/A')).replace('|', '\|')
                        f.write(f"| {name} | {version} | {publisher} | {location} | {size} | {status} | {remarks} | {hive} | {reg_key} |\n") # V7
                if comp_count == 0:
                     f.write("| No components/drivers found or filtering disabled. | | | | | | | | |\n") # V7

        print(f"Inventory successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving Markdown file: {e}")

if __name__ == "__main__":
    print("Software Inventory and Path Validator v7") # Updated version
    print("=" * 40)

    OUTPUT_JSON = True 
    OUTPUT_MARKDOWN = True 
    MARKDOWN_INCLUDE_COMPONENTS = True # Let's include components by default in MD for better overview
    CONSOLE_INCLUDE_COMPONENTS = False 
    
    print("Scanning system... This might take a moment, especially for disk size calculations.")
    all_software = get_installed_software()
    print("Scan complete.")

    if CONSOLE_INCLUDE_COMPONENTS:
        console_apps_to_display = all_software
    else:
        console_apps_to_display = [app for app in all_software if app.get('Category') == "Application"]
        
    if console_apps_to_display:
        print(f"\nFound {len(console_apps_to_display)} applications (defaulting to no components/drivers for console):\n")
        # V7: Added Size and Remarks, adjusted widths
        print(f"{'Application Name':<35} | {'Ver.':<10} | {'Publisher':<20} | {'Install Path':<35} | {'Size':<10} | {'Status':<15} | {'Remarks':<25} | {'Src':<10} | {'Registry Key Path':<50}")
        print("-" * 230) # Adjusted separator length

        for app in console_apps_to_display:
            name = str(app.get('DisplayName', 'N/A'))
            version = str(app.get('DisplayVersion', 'N/A'))
            publisher = str(app.get('Publisher', 'N/A'))
            location = str(app.get('InstallLocation', 'N/A')) 
            size = str(app.get('InstallLocationSize', 'N/A')) # V7
            status = str(app.get('PathStatus', 'N/A'))
            remarks = str(app.get('Remarks', '')) # V7
            hive = str(app.get('SourceHive', 'N/A'))
            reg_key = str(app.get('RegistryKeyPath', 'N/A')) 
            
            name = (name[:32] + '...') if len(name) > 35 else name
            version = (version[:7] + '...') if len(version) > 10 else version
            publisher = (publisher[:17] + '...') if len(publisher) > 20 else publisher
            location = (location[:32] + '...') if len(location) > 35 else location
            # Size is usually short, no truncation needed for 10 chars
            status = (status[:12] + '...') if len(status) > 15 else status
            remarks = (remarks[:22] + '...') if len(remarks) > 25 else remarks
            hive = (hive[:7] + '...') if len(hive) > 10 else hive
            
            reg_key_display = reg_key 
            if len(reg_key_display) > 50: 
                 reg_key_display = "..." + reg_key_display[-(50-3):]

            print(f"{name:<35} | {version:<10} | {publisher:<20} | {location:<35} | {size:<10} | {status:<15} | {remarks:<25} | {hive:<10} | {reg_key_display:<50}")
    else:
        print("No primary applications found (or all were filtered as components/drivers).")

    if OUTPUT_JSON:
        output_to_json(all_software) 
    
    if OUTPUT_MARKDOWN:
        # V7: Changed default to True for MARKDOWN_INCLUDE_COMPONENTS for a fuller report
        output_to_markdown(all_software, include_components=MARKDOWN_INCLUDE_COMPONENTS)

    print("\n" + "=" * 40)
    print("Script finished.")
    print("Note: The script may take a while to run, especially for disk size calculations.") 