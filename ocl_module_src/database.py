import sqlite3
from datetime import datetime
import os

# Database file path (alongside database.py)
DB_FILE = os.path.join(os.path.dirname(__file__), "system_sage_olb.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON;") # Ensure foreign key constraints are enforced
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    creation_date TEXT NOT NULL,
                    last_modified_date TEXT NOT NULL
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    setting_name TEXT NOT NULL,
                    setting_value TEXT,
                    value_type TEXT,
                    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE,
                    UNIQUE (profile_id, category, setting_name)
                )
            """)

            # Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    log_text TEXT NOT NULL,
                    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            print("Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        raise

# --- Profile Functions ---
def _update_profile_last_modified(conn, profile_id: int):
    """Helper to update the last_modified_date of a profile."""
    now_iso = datetime.now().isoformat()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE profiles SET last_modified_date = ? WHERE id = ?", (now_iso, profile_id))
        # conn.commit() is handled by the calling function's context manager
    except sqlite3.Error as e:
        print(f"Error updating profile last_modified_date for profile_id {profile_id}: {e}")
        # Potentially re-raise or handle as appropriate

def create_profile(name: str, description: str | None = None) -> int | None:
    """Inserts a new profile. Returns new profile ID or None on error."""
    now_iso = datetime.now().isoformat()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO profiles (name, description, creation_date, last_modified_date) VALUES (?, ?, ?, ?)",
                (name, description, now_iso, now_iso)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error creating profile: {e}")
        return None

def get_profile(profile_id: int) -> dict | None:
    """Fetches a profile by ID. Returns a dict or None if not found or on error."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error getting profile {profile_id}: {e}")
        return None

def list_all_profiles() -> list[dict]:
    """Fetches all profiles (id, name, description, last_modified_date)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, last_modified_date FROM profiles ORDER BY last_modified_date DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error listing profiles: {e}")
        return []

def update_profile(profile_id: int, name: str | None = None, description: str | None = None) -> bool:
    """Updates name and/or description. Updates last_modified_date. Returns True on success."""
    if name is None and description is None:
        return False # Nothing to update

    fields_to_update = []
    params = []
    if name is not None:
        fields_to_update.append("name = ?")
        params.append(name)
    if description is not None:
        fields_to_update.append("description = ?")
        params.append(description)

    now_iso = datetime.now().isoformat()
    fields_to_update.append("last_modified_date = ?")
    params.append(now_iso)
    params.append(profile_id)

    sql = f"UPDATE profiles SET {', '.join(fields_to_update)} WHERE id = ?"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating profile {profile_id}: {e}")
        return False

def delete_profile(profile_id: int) -> bool:
    """Deletes a profile (settings and logs should cascade delete). Returns True on success."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting profile {profile_id}: {e}")
        return False

# --- Settings Functions ---
def add_setting(profile_id: int, category: str, setting_name: str, setting_value: str, value_type: str) -> int | None:
    """Adds a new setting. Updates profile's last_modified_date. Returns new setting ID or None."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO settings (profile_id, category, setting_name, setting_value, value_type) VALUES (?, ?, ?, ?, ?)",
                (profile_id, category, setting_name, setting_value, value_type)
            )
            _update_profile_last_modified(conn, profile_id)
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding setting for profile {profile_id}: {e}")
        return None

def get_settings_for_profile(profile_id: int) -> list[dict]:
    """Fetches all settings for a profile."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM settings WHERE profile_id = ? ORDER BY category, setting_name", (profile_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting settings for profile {profile_id}: {e}")
        return []

def _get_profile_id_for_setting(conn, setting_id: int) -> int | None:
    """Helper to get profile_id for a given setting_id."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT profile_id FROM settings WHERE id = ?", (setting_id,))
        row = cursor.fetchone()
        return row['profile_id'] if row else None
    except sqlite3.Error as e:
        print(f"Error getting profile_id for setting {setting_id}: {e}")
        return None

def update_setting_value(setting_id: int, setting_value: str) -> bool:
    """Updates the value of an existing setting by its ID. Updates profile's last_modified_date. Returns True on success."""
    try:
        with get_db_connection() as conn:
            profile_id = _get_profile_id_for_setting(conn, setting_id)
            if not profile_id:
                print(f"Setting {setting_id} not found or profile_id could not be retrieved.")
                return False

            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET setting_value = ? WHERE id = ?", (setting_value, setting_id))
            _update_profile_last_modified(conn, profile_id)
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating setting {setting_id}: {e}")
        return False

def delete_setting(setting_id: int) -> bool:
    """Deletes a setting by its ID. Updates profile's last_modified_date. Returns True on success."""
    try:
        with get_db_connection() as conn:
            profile_id = _get_profile_id_for_setting(conn, setting_id)
            if not profile_id:
                print(f"Setting {setting_id} not found or profile_id could not be retrieved for last_modified update.")
                # Still attempt delete if profile_id not found, as the setting itself might exist
                # but this scenario should ideally not happen with valid setting_id

            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE id = ?", (setting_id,))
            if cursor.rowcount > 0 and profile_id:
                 _update_profile_last_modified(conn, profile_id)
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting setting {setting_id}: {e}")
        return False

# --- Log Functions ---
def add_log_entry(profile_id: int, log_text: str) -> int | None:
    """Adds a new log entry. Updates profile's last_modified_date. Returns new log ID or None."""
    now_iso = datetime.now().isoformat()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO logs (profile_id, timestamp, log_text) VALUES (?, ?, ?)",
                (profile_id, now_iso, log_text)
            )
            _update_profile_last_modified(conn, profile_id)
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding log entry for profile {profile_id}: {e}")
        return None

def get_logs_for_profile(profile_id: int) -> list[dict]:
    """Fetches all logs for a profile, ordered by timestamp."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM logs WHERE profile_id = ? ORDER BY timestamp DESC", (profile_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error getting logs for profile {profile_id}: {e}")
        return []

# Initialize the database (create tables if they don't exist)
# This will be called once when the module is first imported.
if __name__ == '__main__':
    # For testing purposes, you can run this script directly
    print(f"Database file will be created at: {DB_FILE}")
    init_db()

    # Example Usage (optional, for direct script run)
    # profile_id = create_profile("Test BIOS Settings", "ASRock X670E Taichi Carrara")
    # if profile_id:
    #     print(f"Created profile with ID: {profile_id}")
    #     add_setting(profile_id, "CPU", "PBO", "Enhanced Mode 4", "str")
    #     add_setting(profile_id, "Memory", "EXPO", "6000CL30", "str")
    #     add_log_entry(profile_id, "Initial setup, testing stability.")
    #     print(f"Settings for profile {profile_id}: {get_settings_for_profile(profile_id)}")
    #     print(f"Logs for profile {profile_id}: {get_logs_for_profile(profile_id)}")
    #     print(f"All profiles: {list_all_profiles()}")
    #     update_profile(profile_id, description="ASRock X670E Taichi - Updated description")
    #     print(f"Profile {profile_id} after update: {get_profile(profile_id)}")

        # settings_list = get_settings_for_profile(profile_id)
        # if settings_list:
        #     setting_to_update_id = settings_list[0]['id']
        #     update_setting_value(setting_to_update_id, "Disabled")
        #     print(f"Settings for profile {profile_id} after update: {get_settings_for_profile(profile_id)}")

        #     setting_to_delete_id = settings_list[1]['id']
        #     delete_setting(setting_to_delete_id)
        #     print(f"Settings for profile {profile_id} after delete: {get_settings_for_profile(profile_id)}")

        # delete_profile(profile_id)
        # print(f"All profiles after delete: {list_all_profiles()}")

else:
    # Ensure DB is initialized when module is imported elsewhere
    init_db()
