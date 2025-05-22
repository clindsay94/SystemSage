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

# --- Configuration (Defaults, will be overridden by argparse) ---
DEFAULT_CALCULATE_DISK_USAGE = True
DEFAULT_OUTPUT_JSON = True
DEFAULT_OUTPUT_MARKDOWN = True
DEFAULT_MARKDOWN_INCLUDE_COMPONENTS = True 
DEFAULT_CONSOLE_INCLUDE_COMPONENTS = False
DEFAULT_OUTPUT_DIR = "output" # V1.2: Default output directory name

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

LAUNCHER_HINTS = {
    "Steam Game": {"publishers": ["valve"], "paths": ["steamapps"]},
    "Epic Games Store Game": {"publishers": ["epic games, inc."], "paths": ["epic games"]},
    "GOG Galaxy Game": {"publishers": ["gog.com"], "paths": ["gog galaxy"]},
    "Battle.net Game": {"publishers": ["blizzard entertainment"], "paths": ["battle.net"]},
    "EA App Game": {"publishers": ["electronic arts"], "paths": ["ea app", "origin games"]},
    "Ubisoft Connect Game": {"publishers": ["ubisoft"], "paths": ["ubisoft game launcher"]},
    "Xbox Game": {"publishers": ["microsoft"], "paths": ["windowsapps", "xboxgames"]}, 
    "Microsoft Store App": {"publishers": [], "paths": ["windowsapps"]}, 
}

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
                                        app_details['Remarks'] += " Registry entry only (Potential Orphan?);" 
                            except FileNotFoundError:
                                app_details['InstallLocation'] = "N/A"
                                app_details['PathStatus'] = "No Path in Registry"
                                if app_details['Category'] == "Application":
                                     app_details['Remarks'] += " Registry entry only (Potential Orphan?);" 
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

def output_to_json(software_list, output_dir, filename="system_sage_inventory.json"): # V1.2: Added output_dir
    """Saves the software list to a JSON file in the specified output directory."""
    try:
        os.makedirs(output_dir, exist_ok=True) # V1.2: Create output directory if it doesn't exist
        full_path = os.path.join(output_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(software_list, f, ensure_ascii=False, indent=4)
        print(f"\nInventory successfully saved to {full_path}")
    except Exception as e:
        print(f"Error saving JSON file to {output_dir}: {e}")

def output_to_markdown(software_list, output_dir, filename="system_sage_inventory.md", include_components=False): # V1.2: Added output_dir
    """Saves the software list to a Markdown file in the specified output directory."""
    try:
        os.makedirs(output_dir, exist_ok=True) # V1.2: Create output directory if it doesn't exist
        full_path = os.path.join(output_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"# System Sage Software Inventory - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            header = "| Application Name | Version | Publisher | Install Path | Size | Status | Remarks | Source Hive | Registry Key Path |\n"
            separator = "|---|---|---|---|---|---|---|---|---|\n"

            f.write("## Applications\n")
            f.write(header)
            f.write(separator)
            app_count = 0
            for app in software_list:
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

            if include_components:
                f.write("\n## Components & Drivers\n")
                f.write(header.replace("Application Name", "Component Name")) 
                f.write(separator)
                comp_count = 0
                for app in software_list:
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
            
            f.write("\n## Future Interactive Features (Planned)\n")
            f.write("The following interactive features are planned for future versions of System Sage, focusing on direct user management capabilities:\n\n")
            f.write("### Interactive Features & Management\n")
            f.write("- **Interactive Orphan/Bad Path Management:**\n")
            f.write("  - Guided review for entries flagged as \"Potential Orphan?\" or \"Broken install path.\"\n")
            f.write("  - Tools to attempt automated file system searches for orphaned entries.\n")
            f.write("  - User-confirmed actions to update incorrect `InstallLocation` values in the registry.\n")
            f.write("  - User-confirmed actions to securely back up and offer deletion of orphaned registry keys.\n")
            f.write("- **Desktop Shortcut Management:**\n")
            f.write("  - List and analyze desktop shortcuts (.lnk files).\n")
            f.write("  - Flag broken shortcuts or those pointing to uninstalled applications.\n")
            f.write("  - Offer interactive options to clean up or repair problematic shortcuts.\n")
            # Add other top-level items from README's "Interactive Features & Management" if they fit the "direct output" context.
            # For now, the above two are the most direct from the README's section.
            f.write("\n*Disclaimer: Modifying the Windows Registry or file system carries risks. Future interactive features will be designed with safety and user confirmation as top priorities. Always ensure you have backups before making significant system changes.*\n")

        print(f"Inventory successfully saved to {full_path}")
    except Exception as e:
        print(f"Error saving Markdown file to {output_dir}: {e}")


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

    args = parser.parse_args()

    if args.markdown_include_components_flag:
        final_markdown_include_components = True
    elif args.markdown_no_components_flag:
        final_markdown_include_components = False
    else:
        final_markdown_include_components = DEFAULT_MARKDOWN_INCLUDE_COMPONENTS

    if args.console_include_components_flag:
        final_console_include_components = True
    elif args.console_no_components_flag:
        final_console_include_components = False
    else:
        final_console_include_components = DEFAULT_CONSOLE_INCLUDE_COMPONENTS

    print("Software Inventory and Path Validator v1.2")
    print("=" * 40)
    
    if args.calculate_disk_usage:
        print("Scanning system... Disk size calculation is ENABLED and might take some time.")
    else:
        print("Scanning system... Disk size calculation is DISABLED.")
        
    all_software = get_installed_software(args.calculate_disk_usage) 
    print("Scan complete.")

    if final_console_include_components: 
        console_apps_to_display = all_software
        print(f"\nFound {len(console_apps_to_display)} total entries (including components/drivers):\n")
    else:
        console_apps_to_display = [app for app in all_software if app.get('Category') == "Application"]
        print(f"\nFound {len(console_apps_to_display)} applications (use --console-include-components to show all entries):\n")
        
    if console_apps_to_display:
        print(f"{'Application Name':<35} | {'Ver.':<10} | {'Publisher':<20} | {'Install Path':<35} | {'Size':<15} | {'Status':<15} | {'Remarks':<30} | {'Src':<10} | {'Registry Key Path':<50}")
        print("-" * 250)

        for app in console_apps_to_display:
            name = str(app.get('DisplayName', 'N/A'))
            version = str(app.get('DisplayVersion', 'N/A'))
            publisher = str(app.get('Publisher', 'N/A'))
            location = str(app.get('InstallLocation', 'N/A')) 
            size = str(app.get('InstallLocationSize', 'N/A')) 
            status = str(app.get('PathStatus', 'N/A'))
            remarks = str(app.get('Remarks', '')) 
            hive = str(app.get('SourceHive', 'N/A'))
            reg_key = str(app.get('RegistryKeyPath', 'N/A')) 
            
            name = (name[:32] + '...') if len(name) > 35 else name
            version = (version[:7] + '...') if len(version) > 10 else version
            publisher = (publisher[:17] + '...') if len(publisher) > 20 else publisher
            location = (location[:32] + '...') if len(location) > 35 else location
            size = (size[:12] + '...') if len(size) > 15 else size
            status = (status[:12] + '...') if len(status) > 15 else status
            remarks = (remarks[:27] + '...') if len(remarks) > 30 else remarks
            hive = (hive[:7] + '...') if len(hive) > 10 else hive
            
            reg_key_display = reg_key 
            if len(reg_key_display) > 50: 
                 reg_key_display = "..." + reg_key_display[-(50-3):]

            print(f"{name:<35} | {version:<10} | {publisher:<20} | {location:<35} | {size:<15} | {status:<15} | {remarks:<30} | {hive:<10} | {reg_key_display:<50}")
    else:
        if final_console_include_components:
             print("No software entries found in the registry.")
        else:
            print("No primary applications found (or all were filtered as components/drivers). Try --console-include-components to see all entries.")

    # V1.2: Use args.output_dir for file paths
    if args.output_json: 
        output_to_json(all_software, args.output_dir) 
    
    if args.output_markdown: 
        output_to_markdown(all_software, args.output_dir, include_components=final_markdown_include_components) 

    print("\n" + "=" * 40)
    print("Script finished.")
