import unittest
import logging
import io
import sys
from unittest.mock import patch, MagicMock
import sqlite3

# Add project root to path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ocl_module_src import olb_api
from ocl_module_src import database

class TestSecurityFix(unittest.TestCase):
    def setUp(self):
        # Configure logging to capture output
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        logging.getLogger("ocl_module_src").addHandler(self.handler)
        logging.getLogger("ocl_module_src").setLevel(logging.ERROR)

    def tearDown(self):
        logging.getLogger("ocl_module_src").removeHandler(self.handler)

    @patch("ocl_module_src.database.sqlite3.connect")
    def test_get_all_profiles_exception_logged_not_printed(self, mock_connect):
        # Force an exception in the database layer
        mock_connect.side_effect = sqlite3.Error("Simulated Database Error")

        # Capture stdout
        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        try:
            # This should trigger the exception and the new error handling
            result = olb_api.get_all_profiles()

            # Reset stdout
            sys.stdout = sys.__stdout__

            # 1. Check that result is the expected default (empty list)
            self.assertEqual(result, [])

            # 2. Check that NOTHING was printed to stdout containing the error
            stdout_content = captured_stdout.getvalue()
            self.assertNotIn("Simulated Database Error", stdout_content)
            self.assertNotIn("API Error in get_all_profiles", stdout_content)

            # 3. Check that the error WAS logged to our logger
            log_content = self.log_capture.getvalue()
            # It might be caught and logged by the database layer first
            self.assertTrue("API Error in get_all_profiles" in log_content or "Error listing profiles" in log_content)
            self.assertIn("Simulated Database Error", log_content)

        finally:
            sys.stdout = sys.__stdout__

    @patch("ocl_module_src.database.sqlite3.connect")
    def test_database_init_db_exception_logged_not_printed(self, mock_connect):
        # Force an exception in the database layer
        mock_connect.side_effect = sqlite3.Error("Simulated DB Init Error")

        # Capture stdout
        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        try:
            # database.init_db() re-raises the exception after logging
            with self.assertRaises(sqlite3.Error):
                database.init_db()

            # Reset stdout
            sys.stdout = sys.__stdout__

            # 1. Check that NOTHING was printed to stdout containing the error
            stdout_content = captured_stdout.getvalue()
            self.assertNotIn("Simulated DB Init Error", stdout_content)
            self.assertNotIn("Database initialization error", stdout_content)

            # 2. Check that the error WAS logged
            log_content = self.log_capture.getvalue()
            self.assertIn("Database initialization error", log_content)
            self.assertIn("Simulated DB Init Error", log_content)

        finally:
            sys.stdout = sys.__stdout__

if __name__ == "__main__":
    unittest.main()
