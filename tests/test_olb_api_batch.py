import unittest
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from ocl_module_src import database, olb_api

class TestOLBAPIBatch(unittest.TestCase):
    def setUp(self):
        # Use a separate test database
        database.DB_FILE = os.path.join(os.getcwd(), "ocl_module_src", "test_system_sage_olb.db")
        if os.path.exists(database.DB_FILE):
            os.remove(database.DB_FILE)
        database.init_db()

    def tearDown(self):
        if os.path.exists(database.DB_FILE):
            os.remove(database.DB_FILE)

    def test_create_new_profile_with_batch(self):
        name = "Test Profile"
        description = "Test Description"
        settings = [
            {"category": "C1", "setting_name": "S1", "setting_value": "V1", "value_type": "str"},
            {"category": "C2", "setting_name": "S2", "setting_value": "V2", "value_type": "str"},
        ]
        logs = ["Log 1", "Log 2"]

        profile_id = olb_api.create_new_profile(name, description, settings, logs)
        self.assertIsNotNone(profile_id)

        # Verify settings
        db_settings = database.get_settings_for_profile(profile_id)
        self.assertEqual(len(db_settings), 2)
        self.assertEqual(db_settings[0]["setting_name"], "S1")
        self.assertEqual(db_settings[1]["setting_name"], "S2")

        # Verify logs
        db_logs = database.get_logs_for_profile(profile_id)
        self.assertEqual(len(db_logs), 2)
        # Logs are ordered DESC by timestamp
        log_texts = [log["log_text"] for log in db_logs]
        self.assertIn("Log 1", log_texts)
        self.assertIn("Log 2", log_texts)

    def test_update_existing_profile_with_batch(self):
        profile_id = olb_api.create_new_profile("Update Test")

        settings_to_add = [
            {"category": "C1", "setting_name": "S1", "setting_value": "V1", "value_type": "str"},
        ]
        logs_to_add = ["New Log"]

        success = olb_api.update_existing_profile(
            profile_id,
            settings_to_add=settings_to_add,
            logs_to_add=logs_to_add
        )
        self.assertTrue(success)

        # Verify settings
        db_settings = database.get_settings_for_profile(profile_id)
        self.assertEqual(len(db_settings), 1)
        self.assertEqual(db_settings[0]["setting_name"], "S1")

        # Verify logs
        db_logs = database.get_logs_for_profile(profile_id)
        self.assertEqual(len(db_logs), 1)
        self.assertEqual(db_logs[0]["log_text"], "New Log")

if __name__ == "__main__":
    unittest.main()
