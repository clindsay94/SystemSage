"""
Internal Python API for the Overclocker's Logbook (OLB) module.
This API provides functions to interact with the OLB database,
encapsulating data access logic and offering higher-level operations.
"""
from typing import List, Dict, Optional, Any
from . import database

# --- Profile API Functions ---

def get_all_profiles() -> List[Dict[str, Any]]:
    """
    Retrieves a summary list of all profiles.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                              represents a profile summary (id, name, description, last_modified_date).
                              Returns an empty list if no profiles exist or an error occurs.
    """
    try:
        return database.list_all_profiles()
    except Exception as e:
        print(f"API Error in get_all_profiles: {e}")
        return []

def get_profile_details(profile_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves detailed information for a specific profile, including its settings and logs.

    Args:
        profile_id (int): The ID of the profile to retrieve.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the profile details (id, name,
                                  description, creation_date, last_modified_date),
                                  along with 'settings' (list of setting dicts) and
                                  'logs' (list of log dicts).
                                  Returns None if the profile is not found or an error occurs.
    """
    try:
        profile_data = database.get_profile(profile_id)
        if not profile_data:
            return None

        settings_data = database.get_settings_for_profile(profile_id)
        logs_data = database.get_logs_for_profile(profile_id)

        # Ensure profile_data is mutable if it's a sqlite3.Row
        detailed_profile = dict(profile_data)
        detailed_profile['settings'] = settings_data
        detailed_profile['logs'] = logs_data

        return detailed_profile
    except Exception as e:
        print(f"API Error in get_profile_details for profile_id {profile_id}: {e}")
        return None

def create_new_profile(
    name: str,
    description: Optional[str] = None,
    initial_settings: Optional[List[Dict[str, Any]]] = None,
    initial_logs: Optional[List[str]] = None
) -> Optional[int]:
    """
    Creates a new profile with optional initial settings and log entries.

    Args:
        name (str): The name for the new profile.
        description (Optional[str]): An optional description for the profile.
        initial_settings (Optional[List[Dict[str, Any]]]): A list of settings to add.
            Each setting dict should have 'category', 'setting_name', 'setting_value', 'value_type'.
        initial_logs (Optional[List[str]]): A list of log text strings to add.

    Returns:
        Optional[int]: The ID of the newly created profile, or None if creation fails.
    """
    try:
        profile_id = database.create_profile(name, description)
        if profile_id is None:
            print(f"API: Failed to create profile entry for '{name}'.")
            return None

        if initial_settings:
            for setting in initial_settings:
                db_setting_id = database.add_setting(
                    profile_id,
                    setting['category'],
                    setting['setting_name'],
                    setting['setting_value'],
                    setting['value_type']
                )
                if db_setting_id is None:
                    print(f"API: Failed to add initial setting '{setting['setting_name']}' for profile {profile_id}.")
                    # Continue adding other settings/logs, or decide on stricter error handling

        if initial_logs:
            for log_text in initial_logs:
                db_log_id = database.add_log_entry(profile_id, log_text)
                if db_log_id is None:
                    print(f"API: Failed to add initial log for profile {profile_id}: '{log_text[:50]}...'.")
                    # Continue adding other logs, or decide on stricter error handling

        return profile_id
    except Exception as e:
        print(f"API Error in create_new_profile for '{name}': {e}")
        return None

def update_existing_profile(
    profile_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    settings_to_add: Optional[List[Dict[str, Any]]] = None,
    settings_to_update: Optional[List[Dict[str, Any]]] = None,
    setting_ids_to_delete: Optional[List[int]] = None,
    logs_to_add: Optional[List[str]] = None
) -> bool:
    """
    Updates an existing profile, its settings, and/or logs.

    Args:
        profile_id (int): The ID of the profile to update.
        name (Optional[str]): New name for the profile.
        description (Optional[str]): New description for the profile.
        settings_to_add (Optional[List[Dict[str, Any]]]): List of settings to add.
        settings_to_update (Optional[List[Dict[str, Any]]]): List of settings to update.
            Each dict should have 'id' (setting_id) and 'setting_value'.
        setting_ids_to_delete (Optional[List[int]]): List of setting IDs to delete.
        logs_to_add (Optional[List[str]]): List of log text strings to add.

    Returns:
        bool: True if any update operation was attempted (even if some sub-operations fail),
              False if the profile doesn't exist or no update parameters were provided.
    """
    attempted_any_update = False
    try:
        if database.get_profile(profile_id) is None:
            print(f"API: Profile with ID {profile_id} not found for update.")
            return False

        if name is not None or description is not None:
            database.update_profile(profile_id, name, description)
            attempted_any_update = True # update_profile itself returns bool, but we track attempt

        if settings_to_add:
            attempted_any_update = True
            for setting in settings_to_add:
                database.add_setting(
                    profile_id,
                    setting['category'],
                    setting['setting_name'],
                    setting['setting_value'],
                    setting['value_type']
                )

        if settings_to_update:
            attempted_any_update = True
            for setting_update in settings_to_update:
                database.update_setting_value(setting_update['id'], setting_update['setting_value'])

        if setting_ids_to_delete:
            attempted_any_update = True
            for setting_id in setting_ids_to_delete:
                database.delete_setting(setting_id)

        if logs_to_add:
            attempted_any_update = True
            for log_text in logs_to_add:
                database.add_log_entry(profile_id, log_text)

        return attempted_any_update
    except Exception as e:
        print(f"API Error in update_existing_profile for profile_id {profile_id}: {e}")
        # If an error occurs during one of the operations, we might still have attempted updates.
        # Depending on desired behavior, could return False here or rely on attempted_any_update.
        return attempted_any_update # Or False if strict success for all parts is needed

def delete_profile_by_id(profile_id: int) -> bool:
    """
    Deletes a profile and its associated settings and logs (due to CASCADE).

    Args:
        profile_id (int): The ID of the profile to delete.

    Returns:
        bool: True if the profile was successfully deleted, False otherwise.
    """
    try:
        return database.delete_profile(profile_id)
    except Exception as e:
        print(f"API Error in delete_profile_by_id for profile_id {profile_id}: {e}")
        return False

def add_log_to_profile(profile_id: int, log_text: str) -> Optional[int]:
    """
    Adds a log entry to a specific profile.

    Args:
        profile_id (int): The ID of the profile to add the log to.
        log_text (str): The text content of the log entry.

    Returns:
        Optional[int]: The ID of the newly created log entry, or None if it fails.
    """
    try:
        if database.get_profile(profile_id) is None: # Check if profile exists
            print(f"API: Profile with ID {profile_id} not found for adding log.")
            return None
        log_id = database.add_log_entry(profile_id, log_text)
        return log_id
    except Exception as e:
        print(f"API Error in add_log_to_profile for profile_id {profile_id}: {e}")
        return None

if __name__ == '__main__':
    # Example usage (requires database.py and system_sage_olb.db to be initialized)
    print("Running OLB API examples...")

    # Ensure DB is clean for a fresh run of examples (optional)
    # import os
    # db_path = os.path.join(os.path.dirname(__file__), "system_sage_olb.db")
    # if os.path.exists(db_path):
    #     os.remove(db_path)
    # database.init_db() # Re-initialize

    print("\n--- Testing get_all_profiles (initially) ---")
    profiles = get_all_profiles()
    print(f"Initial profiles: {profiles}")

    print("\n--- Testing create_new_profile ---")
    profile1_settings = [
        {'category': 'CPU', 'setting_name': 'CoreVoltage', 'setting_value': '1.25', 'value_type': 'float'},
        {'category': 'Memory', 'setting_name': 'Frequency', 'setting_value': '6000', 'value_type': 'int'}
    ]
    profile1_logs = ["Initial stability test passed.", "Increased PBO limits."]
    new_profile_id1 = create_new_profile("My Awesome OC", "Daily driver overclock for Ryzen 9", profile1_settings, profile1_logs)
    if new_profile_id1:
        print(f"Created profile ID: {new_profile_id1}")
    else:
        print("Failed to create profile 1.")

    new_profile_id2 = create_new_profile("Gaming Profile", "Max performance for gaming", initial_logs=["Baseline test."])
    if new_profile_id2:
        print(f"Created profile ID: {new_profile_id2}")
    else:
        print("Failed to create profile 2.")

    print("\n--- Testing get_all_profiles (after creation) ---")
    profiles = get_all_profiles()
    print(f"Profiles after creation: {profiles}")

    if new_profile_id1:
        print(f"\n--- Testing get_profile_details for ID {new_profile_id1} ---")
        details = get_profile_details(new_profile_id1)
        if details:
            print(f"Details for profile {new_profile_id1}:")
            print(f"  ID: {details.get('id')}")
            print(f"  Name: {details.get('name')}")
            print(f"  Description: {details.get('description')}")
            print(f"  Settings: {len(details.get('settings', []))} items")
            for setting in details.get('settings', []):
                print(f"    - {setting.get('category')}/{setting.get('setting_name')}: {setting.get('setting_value')}")
            print(f"  Logs: {len(details.get('logs', []))} items")
            for log in details.get('logs', []):
                print(f"    - [{log.get('timestamp')}]: {log.get('log_text')}")
        else:
            print(f"Could not get details for profile {new_profile_id1}")

    if new_profile_id1:
        print(f"\n--- Testing update_existing_profile for ID {new_profile_id1} ---")
        profile1_settings_to_add = [
            {'category': 'FanControl', 'setting_name': 'CPU_Fan_Curve', 'setting_value': 'Aggressive', 'value_type': 'str'}
        ]
        # Assuming the first setting for profile 1 was CPU CoreVoltage with ID 1 (if DB is fresh)
        # This requires knowing the setting ID, which is dynamic.
        # For a robust test, we'd fetch settings first to get an ID.
        # For this example, let's assume we know a setting ID if one exists.
        profile1_details_before_update = get_profile_details(new_profile_id1)
        setting_to_update_id = None
        if profile1_details_before_update and profile1_details_before_update['settings']:
            setting_to_update_id = profile1_details_before_update['settings'][0]['id'] # Get ID of first setting

        profile1_settings_to_update = []
        if setting_to_update_id:
            profile1_settings_to_update.append({'id': setting_to_update_id, 'setting_value': '1.28'}) # Update CoreVoltage
            print(f"Attempting to update setting ID {setting_to_update_id} to 1.28")

        update_success = update_existing_profile(
            new_profile_id1,
            name="My Awesome OC (Rev.2)",
            settings_to_add=profile1_settings_to_add,
            settings_to_update=profile1_settings_to_update,
            logs_to_add=["Performed BIOS update, re-applied settings."]
        )
        print(f"Update attempted for profile {new_profile_id1}: {update_success}")

        print(f"\n--- Testing get_profile_details for ID {new_profile_id1} (after update) ---")
        details_after_update = get_profile_details(new_profile_id1)
        if details_after_update:
            print(f"Details for profile {new_profile_id1} after update:")
            print(f"  Name: {details_after_update.get('name')}")
            print(f"  Settings: {len(details_after_update.get('settings', []))} items")
            for setting in details_after_update.get('settings', []):
                print(f"    - {setting.get('category')}/{setting.get('setting_name')}: {setting.get('setting_value')}")
            print(f"  Logs: {len(details_after_update.get('logs', []))} items")
            for log in details_after_update.get('logs', []):
                print(f"    - [{log.get('timestamp')}]: {log.get('log_text')}")


    if new_profile_id2:
        print(f"\n--- Testing add_log_to_profile for ID {new_profile_id2} ---")
        log_id = add_log_to_profile(new_profile_id2, "Ran FurMark stress test - stable.")
        if log_id:
            print(f"Added log with ID {log_id} to profile {new_profile_id2}")
            details_after_log = get_profile_details(new_profile_id2)
            if details_after_log:
                 print(f"  Logs now: {len(details_after_log.get('logs', []))} items")
        else:
            print(f"Failed to add log to profile {new_profile_id2}")

    if new_profile_id1:
        print(f"\n--- Testing delete_profile_by_id for ID {new_profile_id1} ---")
        delete_success = delete_profile_by_id(new_profile_id1)
        print(f"Deletion of profile {new_profile_id1} successful: {delete_success}")

    print("\n--- Testing get_all_profiles (after actions) ---")
    profiles_after_actions = get_all_profiles()
    print(f"Profiles after actions: {profiles_after_actions}")

    # Test deleting a setting from the remaining profile (if any)
    if new_profile_id2 and get_profile_details(new_profile_id2): # Check if profile still exists
        profile2_details = get_profile_details(new_profile_id2)
        if profile2_details and profile2_details['settings']:
            setting_to_delete_id = profile2_details['settings'][0]['id']
            print(f"\n--- Testing deleting setting ID {setting_to_delete_id} from profile ID {new_profile_id2} ---")
            update_success = update_existing_profile(new_profile_id2, setting_ids_to_delete=[setting_to_delete_id])
            print(f"Update (delete setting) for profile {new_profile_id2} attempted: {update_success}")
            details_after_setting_delete = get_profile_details(new_profile_id2)
            if details_after_setting_delete:
                print(f"  Settings now: {len(details_after_setting_delete.get('settings', []))} items")

    print("\nOLB API examples finished.")
