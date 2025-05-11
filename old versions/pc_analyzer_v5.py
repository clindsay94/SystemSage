# Python Software Inventory & Path Validator v5
# This script queries the Windows Registry to list installed software,
# validates their installation paths, outputs to console, JSON, and Markdown.
# V5: Changed path separators to forward slashes (/) for easier copy-pasting.

import winreg  # Module to access the Windows registry
import os      # Module for operating system dependent functionality, like path checking
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
    """
    Checks if a software entry is likely a component/driver based on keywords.
    """
    name_lower = str(display_name).lower()
    publisher_lower = str(publisher).lower()

    for keyword in COMPONENT_KEYWORDS:
        if keyword in name_lower or keyword in publisher_lower:
            return True
    if name_lower.startswith('{') or name_lower.startswith('kb'):
        return True
    return False

def get_hkey_name(hkey_root):
    """Returns the string name of an HKEY root for display."""
    if hkey_root == winreg.HKEY_LOCAL_MACHINE:
        return "HKEY_LOCAL_MACHINE"
    if hkey_root == winreg.HKEY_CURRENT_USER:
        return "HKEY_CURRENT_USER"
    return str(hkey_root)

def normalize_path_slashes(path_string):
    """Converts all backslashes to forward slashes in a path string."""
    if isinstance(path_string, str):
        return path_string.replace("\\", "/")
    return path_string


def get_installed_software():
    """
    Retrieves a list of installed software from the Windows Registry.
    Checks HKLM (64-bit, 32-bit) and HKCU.
    """
    software_list = []
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (64-bit)"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (32-bit)"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU")
    ]

    processed_entries = set() 

    for hkey_root, path_suffix, hive_display_name in registry_paths:
        try:
            # V5: Normalize path_suffix for constructing full_reg_key_path
            normalized_path_suffix = normalize_path_slashes(path_suffix)
            with winreg.OpenKey(hkey_root, path_suffix) as uninstall_key: # Use original path_suffix for OpenKey
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                    subkey_name = "" 
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        normalized_subkey_name = normalize_path_slashes(subkey_name)
                        
                        # V5: Construct the full registry key path with forward slashes
                        full_reg_key_path = f"{get_hkey_name(hkey_root)}/{normalized_path_suffix}/{normalized_subkey_name}"

                        with winreg.OpenKey(uninstall_key, subkey_name) as app_key:
                            app_details = {
                                'SourceHive': hive_display_name,
                                'RegistryKeyPath': full_reg_key_path 
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
                                
                                # V5: Normalize InstallLocation slashes
                                app_details['InstallLocation'] = normalize_path_slashes(install_location_cleaned)
                                
                                # Use original cleaned path for os.path.exists as it expects OS-native slashes
                                if install_location_cleaned and os.path.exists(install_location_cleaned):
                                    app_details['PathStatus'] = "OK"
                                elif install_location_cleaned:
                                    app_details['PathStatus'] = "Path Not Found"
                                else:
                                    app_details['PathStatus'] = "No Valid Path in Registry"
                            except FileNotFoundError:
                                app_details['InstallLocation'] = "N/A"
                                app_details['PathStatus'] = "No Path in Registry"
                            except OSError:
                                app_details['InstallLocation'] = "Error Reading Path"
                                app_details['PathStatus'] = "Error"

                            app_details['Category'] = "Component/Driver" if is_likely_component(app_details['DisplayName'], app_details['Publisher']) else "Application"
                            
                            if app_details['DisplayName'] and not app_details['DisplayName'].startswith('{'):
                                software_list.append(app_details)
                    except OSError:
                        pass 
                    except Exception as e_inner:
                        pass
        except FileNotFoundError:
            print(f"Registry path not found: {hive_display_name} - {path_suffix}. This might be normal.")
            continue
        except Exception as e_outer:
            print(f"An error occurred accessing registry path {hive_display_name} - {path_suffix}: {e_outer}")
            continue
            
    return sorted(software_list, key=lambda x: str(x.get('DisplayName','')).lower())

def output_to_json(software_list, filename="system_sage_inventory.json"):
    """Saves the software list to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(software_list, f, ensure_ascii=False, indent=4)
        print(f"\nInventory successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

def output_to_markdown(software_list, filename="system_sage_inventory.md", include_components=False):
    """Saves the software list to a Markdown file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# System Sage Software Inventory - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            header = "| Application Name | Version | Publisher | Install Path | Status | Source Hive | Registry Key Path |\n"
            separator = "|---|---|---|---|---|---|---|\n"

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
                    location = str(app.get('InstallLocation', 'N/A')).replace('|', '\|') # Already normalized
                    status = str(app.get('PathStatus', 'N/A')).replace('|', '\|')
                    hive = str(app.get('SourceHive', 'N/A')).replace('|', '\|')
                    reg_key = str(app.get('RegistryKeyPath', 'N/A')).replace('|', '\|') # Already normalized
                    f.write(f"| {name} | {version} | {publisher} | {location} | {status} | {hive} | {reg_key} |\n")
            if app_count == 0:
                f.write("| No primary applications found. | | | | | | |\n")

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
                        location = str(app.get('InstallLocation', 'N/A')).replace('|', '\|') # Already normalized
                        status = str(app.get('PathStatus', 'N/A')).replace('|', '\|')
                        hive = str(app.get('SourceHive', 'N/A')).replace('|', '\|')
                        reg_key = str(app.get('RegistryKeyPath', 'N/A')).replace('|', '\|') # Already normalized
                        f.write(f"| {name} | {version} | {publisher} | {location} | {status} | {hive} | {reg_key} |\n")
                if comp_count == 0:
                     f.write("| No components/drivers found or filtering disabled. | | | | | | |\n")

        print(f"Inventory successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving Markdown file: {e}")

if __name__ == "__main__":
    print("Software Inventory and Path Validator v5") # Updated version
    print("=" * 40)

    OUTPUT_JSON = True 
    OUTPUT_MARKDOWN = True 
    MARKDOWN_INCLUDE_COMPONENTS = False 
    CONSOLE_INCLUDE_COMPONENTS = False 
    
    all_software = get_installed_software()

    if CONSOLE_INCLUDE_COMPONENTS:
        console_apps_to_display = all_software
    else:
        console_apps_to_display = [app for app in all_software if app.get('Category') == "Application"]
        
    if console_apps_to_display:
        print(f"\nFound {len(console_apps_to_display)} applications (defaulting to no components/drivers for console):\n")
        print(f"{'Application Name':<40} | {'Version':<12} | {'Publisher':<25} | {'Install Path':<40} | {'Status':<20} | {'Source':<12} | {'Registry Key Path':<60}")
        print("-" * 220) 

        for app in console_apps_to_display:
            name = str(app.get('DisplayName', 'N/A'))
            version = str(app.get('DisplayVersion', 'N/A'))
            publisher = str(app.get('Publisher', 'N/A'))
            location = str(app.get('InstallLocation', 'N/A')) # Already normalized for internal storage
            status = str(app.get('PathStatus', 'N/A'))
            hive = str(app.get('SourceHive', 'N/A'))
            reg_key = str(app.get('RegistryKeyPath', 'N/A')) # Already normalized for internal storage
            
            name = (name[:37] + '...') if len(name) > 40 else name
            version = (version[:9] + '...') if len(version) > 12 else version
            publisher = (publisher[:22] + '...') if len(publisher) > 25 else publisher
            location = (location[:37] + '...') if len(location) > 40 else location
            status = (status[:17] + '...') if len(status) > 20 else status
            reg_key = (reg_key[:57] + '...') if len(reg_key) > 60 else reg_key

            print(f"{name:<40} | {version:<12} | {publisher:<25} | {location:<40} | {status:<20} | {hive:<12} | {reg_key:<60}")
    else:
        print("No primary applications found (or all were filtered as components/drivers).")

    if OUTPUT_JSON:
        output_to_json(all_software) 
    
    if OUTPUT_MARKDOWN:
        output_to_markdown(all_software, include_components=MARKDOWN_INCLUDE_COMPONENTS)

    print("\n" + "=" * 40)
    print("Script finished.")
