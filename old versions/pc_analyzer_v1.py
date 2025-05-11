# Python Software Inventory & Path Validator v1
# This script queries the Windows Registry to list installed software
# and validates their installation paths.

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
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    for hkey, path_suffix in registry_paths:
        try:
            # Open the main Uninstall registry key
            with winreg.OpenKey(hkey, path_suffix) as uninstall_key:
                # Enumerate over the subkeys, each representing an installed application
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]): # QueryInfoKey returns (num_subkeys, num_values, last_modified_time)
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
                                install_location = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                                app_details['InstallLocation'] = install_location
                                # Validate if the path exists
                                if install_location and os.path.exists(install_location):
                                    app_details['PathStatus'] = "OK"
                                elif install_location: # Path is listed but doesn't exist
                                    app_details['PathStatus'] = "Path Not Found"
                                else: # InstallLocation value is empty
                                    app_details['PathStatus'] = "No Path in Registry"
                            except FileNotFoundError:
                                # InstallLocation is not always present
                                app_details['InstallLocation'] = "N/A"
                                app_details['PathStatus'] = "No Path in Registry"
                            except OSError:
                                app_details['InstallLocation'] = "Error Reading Path"
                                app_details['PathStatus'] = "Error"
                            
                            # Avoid adding entries that are just system components or updates without a clear display name
                            # or if DisplayName seems to be a GUID (common for some updates/patches)
                            if app_details.get('DisplayName') and not app_details['DisplayName'].startswith('{') and not app_details['DisplayName'].startswith('KB') :
                                # Check if this software (based on DisplayName and Version) is already in our list
                                # This handles cases where an app might appear in both registry views (e.g. 32-bit and 64-bit views)
                                # or has multiple entries. We'll take the first one we find with a valid-looking name.
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
                        print(f"Could not open or read subkey: {subkey_name} under {path_suffix}. Skipping.")
                        continue
        except FileNotFoundError:
            print(f"Registry path not found: {hkey}\\{path_suffix}. This might be normal (e.g., on a 32-bit system for WOW6432Node).")
            continue
        except Exception as e:
            print(f"An error occurred accessing registry path {hkey}\\{path_suffix}: {e}")
            continue
            
    return sorted(software_list, key=lambda x: x['DisplayName'].lower()) # Sort alphabetically by display name

if __name__ == "__main__":
    print("Software Inventory and Path Validator v1")
    print("=" * 40)
    
    # A little primer on the Windows Registry for you!
    # The Windows Registry is a hierarchical database that stores low-level settings
    # for the Microsoft Windows operating system and for applications that opt to use the registry.
    # When software is installed, it typically creates entries here to tell Windows
    # about itself - its name, version, publisher, where it's installed, how to uninstall it, etc.
    # Our script is peeking into these records!
    #
    # Common Keys for Installed Software:
    # - HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
    #   (This is a common place for 64-bit applications or system-wide 32-bit applications)
    # - HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall
    #   (On a 64-bit Windows system, this is where 32-bit applications often register themselves.
    #    WOW6432Node stands for "Windows on Windows 64-bit Node" - it's an emulation layer.)
    # - HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
    #   (For software installed only for the current user - we're not checking this one yet for simplicity,
    #    but it's something we could add!)
    #
    # What we're looking for in each application's subkey:
    # - 'DisplayName': The name you see in "Apps & Features" or "Programs and Features".
    # - 'DisplayVersion': The version of the software.
    # - 'Publisher': Who made the software.
    # - 'InstallLocation': The directory where the software is supposedly installed. This is key for our path check!
    #
    # Why path validation is important (as you pointed out!):
    # Sometimes, if an application's folder is moved manually, or if an uninstaller doesn't clean up
    # properly, the registry might still point to the old, non-existent location. This can cause issues.
    # Our 'PathStatus' will help identify these.

    installed_apps = get_installed_software()

    if installed_apps:
        print(f"\nFound {len(installed_apps)} installed applications:\n")
        # Header
        print(f"{'Application Name':<50} | {'Version':<15} | {'Publisher':<30} | {'Install Path':<60} | {'Status'}")
        print("-" * 170) # Print a separator line

        for app in installed_apps:
            name = app.get('DisplayName', 'N/A')
            version = app.get('DisplayVersion', 'N/A')
            publisher = app.get('Publisher', 'N/A')
            location = app.get('InstallLocation', 'N/A')
            status = app.get('PathStatus', 'N/A')
            
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

    # Mini-Lesson: Running this script
    # 1. Save this code as a Python file (e.g., `inventory_check.py`).
    # 2. Open a command prompt (cmd) or PowerShell.
    # 3. Navigate to the directory where you saved the file (e.g., `cd C:\path\to\your\script`).
    # 4. Run the script using: `python inventory_check.py`
    #
    # Potential Issue: Permissions
    # Accessing HKEY_LOCAL_MACHINE in the registry might sometimes require administrator privileges.
    # If the script doesn't show many applications or gives errors, try running your
    # command prompt or PowerShell "as Administrator".
