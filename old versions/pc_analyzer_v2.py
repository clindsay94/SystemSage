# Python Software Inventory & Path Validator v2
# This script queries the Windows Registry to list installed software
# and validates their installation paths.
# V2: Added stripping of quotes from InstallLocation before path validation.

import winreg  # Module to access the Windows registry
import os      # Module for operating system dependent functionality, like path checking

def get_installed_software():
    """
    Retrieves a list of installed software from the Windows Registry.
    It checks both standard locations for 64-bit and 32-bit applications.
    """
    software_list = []
    # Registry paths to check.
    # HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall is for general software
    # HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall is for 32-bit software on 64-bit Windows
    # HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall is for user-specific software (can be added later)
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
        # Consider adding: (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    for hkey, path_suffix in registry_paths:
        try:
            # Open the main Uninstall registry key
            with winreg.OpenKey(hkey, path_suffix) as uninstall_key:
                # Enumerate over the subkeys, each representing an installed application
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]): # QueryInfoKey returns (num_subkeys, num_values, last_modified_time)
                    subkey_name = "" # Initialize to ensure it's defined for the error message
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        with winreg.OpenKey(uninstall_key, subkey_name) as app_key:
                            app_details = {}
                            try:
                                # Attempt to read DisplayName
                                app_details['DisplayName'] = winreg.QueryValueEx(app_key, "DisplayName")[0]
                            except FileNotFoundError:
                                # Some entries might not have a DisplayName, use the subkey name as a fallback
                                app_details['DisplayName'] = subkey_name 
                            except OSError: # Handles other potential errors like incorrect data type
                                app_details['DisplayName'] = f"{subkey_name} (Error reading name)"


                            # Attempt to read DisplayVersion
                            try:
                                app_details['DisplayVersion'] = winreg.QueryValueEx(app_key, "DisplayVersion")[0]
                            except FileNotFoundError:
                                app_details['DisplayVersion'] = "N/A"
                            except OSError:
                                app_details['DisplayVersion'] = "Error"

                            # Attempt to read Publisher
                            try:
                                app_details['Publisher'] = winreg.QueryValueEx(app_key, "Publisher")[0]
                            except FileNotFoundError:
                                app_details['Publisher'] = "N/A"
                            except OSError:
                                app_details['Publisher'] = "Error"

                            # Attempt to read InstallLocation and validate its path
                            try:
                                install_location_raw = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                                
                                # NEW in V2: Strip leading/trailing quotes if they exist
                                install_location_cleaned = install_location_raw
                                if isinstance(install_location_raw, str):
                                    # Remove leading/trailing whitespace first, then quotes
                                    temp_location = install_location_raw.strip()
                                    if (temp_location.startswith('"') and temp_location.endswith('"')) or \
                                       (temp_location.startswith("'") and temp_location.endswith("'")):
                                        install_location_cleaned = temp_location[1:-1]
                                
                                app_details['InstallLocation'] = install_location_cleaned # Store the cleaned path for display
                                
                                # Validate if the cleaned path exists
                                if install_location_cleaned and os.path.exists(install_location_cleaned):
                                    app_details['PathStatus'] = "OK"
                                elif install_location_cleaned: # Path is listed but doesn't exist
                                    app_details['PathStatus'] = "Path Not Found"
                                else: # InstallLocation value was empty or became empty after cleaning
                                    app_details['PathStatus'] = "No Valid Path in Registry"
                            except FileNotFoundError:
                                # InstallLocation is not always present
                                app_details['InstallLocation'] = "N/A"
                                app_details['PathStatus'] = "No Path in Registry"
                            except OSError: # Catch other errors like permission issues or unexpected data types
                                app_details['InstallLocation'] = "Error Reading Path"
                                app_details['PathStatus'] = "Error"
                            
                            # Avoid adding entries that are just system components or updates without a clear display name
                            # or if DisplayName seems to be a GUID (common for some updates/patches)
                            # Also, ensure DisplayName is a string before calling startswith
                            display_name_str = str(app_details.get('DisplayName', ''))
                            if display_name_str and not display_name_str.startswith('{') and not display_name_str.startswith('KB') :
                                # Check if this software (based on DisplayName and Version) is already in our list
                                is_duplicate = False
                                for existing_app in software_list:
                                    if existing_app['DisplayName'] == app_details['DisplayName'] and \
                                       existing_app.get('DisplayVersion') == app_details.get('DisplayVersion'):
                                        is_duplicate = True
                                        break
                                if not is_duplicate:
                                    software_list.append(app_details)
                    except OSError:
                        # This can happen if a subkey is unexpectedly removed or permissions are denied
                        # Or if we try to open a "value" as a "key"
                        print(f"Could not open or read subkey: '{subkey_name}' under {path_suffix}. Skipping.")
                        continue
        except FileNotFoundError:
            print(f"Registry path not found: HKEY_...\\{path_suffix}. This might be normal (e.g., on a 32-bit system for WOW6432Node).")
            continue
        except Exception as e:
            print(f"An error occurred accessing registry path HKEY_...\\{path_suffix}: {e}")
            continue
            
    return sorted(software_list, key=lambda x: str(x.get('DisplayName','')).lower()) # Sort alphabetically

if __name__ == "__main__":
    print("Software Inventory and Path Validator v2")
    print("=" * 40)
    
    # (Mini-lesson and other comments remain largely the same as v1)
    # ...
    # Key change in v2:
    # - We now attempt to strip leading/trailing quotes from 'InstallLocation'
    #   values read from the registry. This can improve accuracy for paths
    #   that are stored with unnecessary quotes. For example, if the registry
    #   has "C:\Games\MyApp" (with quotes), v1 would look for a path that
    #   literally includes quotes. V2 will strip them and check C:\Games\MyApp.

    installed_apps = get_installed_software()

    if installed_apps:
        print(f"\nFound {len(installed_apps)} installed applications:\n")
        # Header
        print(f"{'Application Name':<50} | {'Version':<15} | {'Publisher':<30} | {'Install Path':<60} | {'Status'}")
        print("-" * 170) # Print a separator line

        for app in installed_apps:
            name = str(app.get('DisplayName', 'N/A')) # Ensure string conversion for display
            version = str(app.get('DisplayVersion', 'N/A'))
            publisher = str(app.get('Publisher', 'N/A'))
            location = str(app.get('InstallLocation', 'N/A'))
            status = str(app.get('PathStatus', 'N/A'))
            
            # Truncate long strings to fit the table
            name = (name[:47] + '...') if len(name) > 50 else name
            version = (version[:12] + '...') if len(version) > 15 else version
            publisher = (publisher[:27] + '...') if len(publisher) > 30 else publisher
            location = (location[:57] + '...') if len(location) > 60 else location

            print(f"{name:<50} | {version:<15} | {publisher:<30} | {location:<60} | {status}")
    else:
        print("No installed applications found or could not access registry information.")

    print("\n" + "=" * 40)
    print("Script finished.")

    # (Running instructions remain the same)
    # ...
