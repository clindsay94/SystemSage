# Python Software Inventory & Path Validator v3
# This script queries the Windows Registry to list installed software,
# validates their installation paths, and outputs to console, JSON, and Markdown.
# V3: Added HKCU scanning, JSON/Markdown output, and basic component filtering.

import winreg  # Module to access the Windows registry
import os      # Module for operating system dependent functionality, like path checking
import json    # Module for JSON operations
import datetime # Module to get current timestamp for output files

# --- Configuration for Filtering ---
# Keywords to identify entries that are likely components, drivers, SDKs, etc.
# This list can be expanded. Case-insensitive matching will be used.
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
    # Also filter out entries that are just GUIDs or KB numbers explicitly if not caught by keywords
    if name_lower.startswith('{') or name_lower.startswith('kb'):
        return True
    return False

def get_installed_software():
    """
    Retrieves a list of installed software from the Windows Registry.
    Checks HKLM (64-bit, 32-bit) and HKCU.
    """
    software_list = []
    # V3: Added HKCU path
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (64-bit)"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM (32-bit)"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU")
    ]

    processed_entries = set() # To keep track of (DisplayName, DisplayVersion) to avoid duplicates across hives

    for hkey, path_suffix, hive_name in registry_paths:
        try:
            with winreg.OpenKey(hkey, path_suffix) as uninstall_key:
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                    subkey_name = "" 
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        with winreg.OpenKey(uninstall_key, subkey_name) as app_key:
                            app_details = {'SourceHive': hive_name} # Add source hive info
                            
                            try:
                                app_details['DisplayName'] = str(winreg.QueryValueEx(app_key, "DisplayName")[0])
                            except FileNotFoundError:
                                app_details['DisplayName'] = subkey_name 
                            except OSError:
                                app_details['DisplayName'] = f"{subkey_name} (Error reading name)"

                            # Create a unique identifier for this entry to check for duplicates
                            entry_id = (app_details['DisplayName'], "") # Version might not exist

                            try:
                                app_details['DisplayVersion'] = str(winreg.QueryValueEx(app_key, "DisplayVersion")[0])
                                entry_id = (app_details['DisplayName'], app_details['DisplayVersion'])
                            except FileNotFoundError:
                                app_details['DisplayVersion'] = "N/A"
                            except OSError:
                                app_details['DisplayVersion'] = "Error"
                            
                            if entry_id in processed_entries:
                                continue # Skip if already processed from another hive/path
                            processed_entries.add(entry_id)

                            try:
                                app_details['Publisher'] = str(winreg.QueryValueEx(app_key, "Publisher")[0])
                            except FileNotFoundError:
                                app_details['Publisher'] = "N/A"
                            except OSError:
                                app_details['Publisher'] = "Error"

                            try:
                                install_location_raw = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                                install_location_cleaned = str(install_location_raw) # Ensure it's a string
                                
                                if isinstance(install_location_raw, str):
                                    temp_location = install_location_raw.strip()
                                    if (temp_location.startswith('"') and temp_location.endswith('"')) or \
                                       (temp_location.startswith("'") and temp_location.endswith("'")):
                                        install_location_cleaned = temp_location[1:-1]
                                
                                app_details['InstallLocation'] = install_location_cleaned
                                
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

                            # V3: Add categorization
                            app_details['Category'] = "Component/Driver" if is_likely_component(app_details['DisplayName'], app_details['Publisher']) else "Application"
                            
                            # Filter out entries that are clearly not applications before adding
                            # (already handled by is_likely_component for categorization,
                            # but keeping a basic check here for DisplayName integrity)
                            if app_details['DisplayName'] and not app_details['DisplayName'].startswith('{'):
                                software_list.append(app_details)
                    except OSError:
                        # print(f"Could not open or read subkey: '{subkey_name}' under {path_suffix} ({hive_name}). Skipping.")
                        pass # Suppress these errors for cleaner output, can be enabled for debugging
                    except Exception as e_inner:
                        # print(f"Unexpected error processing subkey '{subkey_name}': {e_inner}")
                        pass
        except FileNotFoundError:
            print(f"Registry path not found: {hive_name} - {path_suffix}. This might be normal.")
            continue
        except Exception as e_outer:
            print(f"An error occurred accessing registry path {hive_name} - {path_suffix}: {e_outer}")
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
            
            f.write("## Applications\n")
            f.write("| Application Name | Version | Publisher | Install Path | Status | Source Hive |\n")
            f.write("|---|---|---|---|---|---|\n")
            app_count = 0
            for app in software_list:
                if app.get('Category') == "Application":
                    app_count +=1
                    name = str(app.get('DisplayName', 'N/A')).replace('|', '\|') # Escape pipe characters for MD
                    version = str(app.get('DisplayVersion', 'N/A')).replace('|', '\|')
                    publisher = str(app.get('Publisher', 'N/A')).replace('|', '\|')
                    location = str(app.get('InstallLocation', 'N/A')).replace('|', '\|')
                    status = str(app.get('PathStatus', 'N/A')).replace('|', '\|')
                    hive = str(app.get('SourceHive', 'N/A')).replace('|', '\|')
                    f.write(f"| {name} | {version} | {publisher} | {location} | {status} | {hive} |\n")
            if app_count == 0:
                f.write("| No primary applications found. |\n")

            if include_components:
                f.write("\n## Components & Drivers\n")
                f.write("| Component Name | Version | Publisher | Install Path | Status | Source Hive |\n")
                f.write("|---|---|---|---|---|---|\n")
                comp_count = 0
                for app in software_list:
                    if app.get('Category') == "Component/Driver":
                        comp_count +=1
                        name = str(app.get('DisplayName', 'N/A')).replace('|', '\|')
                        version = str(app.get('DisplayVersion', 'N/A')).replace('|', '\|')
                        publisher = str(app.get('Publisher', 'N/A')).replace('|', '\|')
                        location = str(app.get('InstallLocation', 'N/A')).replace('|', '\|')
                        status = str(app.get('PathStatus', 'N/A')).replace('|', '\|')
                        hive = str(app.get('SourceHive', 'N/A')).replace('|', '\|')
                        f.write(f"| {name} | {version} | {publisher} | {location} | {status} | {hive} |\n")
                if comp_count == 0:
                     f.write("| No components/drivers found or filtering disabled. |\n")

        print(f"Inventory successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving Markdown file: {e}")

if __name__ == "__main__":
    print("Software Inventory and Path Validator v3")
    print("=" * 40)

    # --- Configuration ---
    OUTPUT_JSON = True  # Set to False to disable JSON output
    OUTPUT_MARKDOWN = True # Set to False to disable Markdown output
    MARKDOWN_INCLUDE_COMPONENTS = False # Set to True to include components/drivers in Markdown
    CONSOLE_INCLUDE_COMPONENTS = False # Set to True to include components/drivers in Console output
    
    # --- Script Execution ---
    all_software = get_installed_software()

    # Filter for console output if needed
    if CONSOLE_INCLUDE_COMPONENTS:
        console_apps_to_display = all_software
    else:
        console_apps_to_display = [app for app in all_software if app.get('Category') == "Application"]
        
    if console_apps_to_display:
        print(f"\nFound {len(console_apps_to_display)} applications (excluding components/drivers by default for console):\n")
        print(f"{'Application Name':<50} | {'Version':<15} | {'Publisher':<30} | {'Install Path':<50} | {'Status':<25} | {'Source':<12}")
        print("-" * 190)

        for app in console_apps_to_display:
            name = str(app.get('DisplayName', 'N/A'))
            version = str(app.get('DisplayVersion', 'N/A'))
            publisher = str(app.get('Publisher', 'N/A'))
            location = str(app.get('InstallLocation', 'N/A'))
            status = str(app.get('PathStatus', 'N/A'))
            hive = str(app.get('SourceHive', 'N/A'))
            
            name = (name[:47] + '...') if len(name) > 50 else name
            version = (version[:12] + '...') if len(version) > 15 else version
            publisher = (publisher[:27] + '...') if len(publisher) > 30 else publisher
            location = (location[:47] + '...') if len(location) > 50 else location
            status = (status[:22] + '...') if len(status) > 25 else status


            print(f"{name:<50} | {version:<15} | {publisher:<30} | {location:<50} | {status:<25} | {hive:<12}")
    else:
        print("No primary applications found (or all were filtered as components/drivers).")

    # --- File Outputs ---
    if OUTPUT_JSON:
        # For JSON, we usually want all data, including components
        output_to_json(all_software) 
    
    if OUTPUT_MARKDOWN:
        output_to_markdown(all_software, include_components=MARKDOWN_INCLUDE_COMPONENTS)

    print("\n" + "=" * 40)
    print("Script finished.")
