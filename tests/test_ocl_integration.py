import unittest
from unittest.mock import patch, MagicMock, call, PropertyMock
import tkinter as tk
from tkinter import ttk # For Treeview
import sys
import os

import customtkinter # Added for CTkTable and CTkTextbox
from CTkTable import CTkTable # Added for CTkTable
import tkinter # Added to define tkinter.Tk for spec

# Adjust path to import SystemSageApp from systemsage_main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from systemsage_main import SystemSageApp # UPDATED

# It's often good practice to mock the entire module that is external to the unit under test.
# We will use @patch decorators for specific test methods or the setUp method for `ocl_api`.

# Patch customtkinter.CTk.__init__ globally to prevent actual Tk window init
MOCK_CTK_INIT_PATCHER = patch('customtkinter.CTk.__init__', MagicMock(return_value=None))
MOCK_CTK_INIT_PATCHER.start()

class TestOCLIntegration(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        """Tear down after all tests in the class."""
        MOCK_CTK_INIT_PATCHER.stop()
        patch.stopall() 

    # Patches for CTk and global functions remain as decorators
    @patch('customtkinter.CTk.title', new_callable=MagicMock)
    @patch('customtkinter.CTk.geometry', new_callable=MagicMock)
    @patch('customtkinter.CTk.option_add', new_callable=MagicMock)
    @patch('customtkinter.set_appearance_mode', new_callable=MagicMock) 
    @patch('customtkinter.set_default_color_theme', new_callable=MagicMock)
    @patch('systemsage_main.SystemSageApp._setup_ui', new_callable=MagicMock)
    def setUp(self, mock_setup_ui, mock_set_default_theme, mock_set_appearance_mode, mock_option_add, mock_geometry, mock_title): # mock_get_all_profiles_func removed
        """Set up for each test.
        Creates an instance of SystemSageApp with a mocked ocl_api.
        """
        # Patch systemsage_main.ocl_api.get_all_profiles manually
        self.ocl_api_get_all_profiles_patcher = patch('systemsage_main.ocl_api.get_all_profiles')
        self.mock_get_all_profiles = self.ocl_api_get_all_profiles_patcher.start()
        
        # Store other mocks if needed for assertions, or just let them be passed
        self.mock_setup_ui = mock_setup_ui 
        self.mock_set_default_theme = mock_set_default_theme
        self.mock_set_appearance_mode = mock_set_appearance_mode
        self.mock_option_add = mock_option_add
        self.mock_geometry = mock_geometry
        self.mock_title = mock_title
        
        # Mock CLI args if the app expects it
        # Create a mock object that can have attributes assigned for argparse results
        self.mock_args = MagicMock()
        self.mock_args.calculate_disk_usage = True
        self.mock_args.output_dir = "output"
        self.mock_args.markdown_include_components_flag = False # Example
        self.mock_args.markdown_no_components_flag = False    # Example
        # Add any other attributes that args might have, which SystemSageApp uses.

        # To prevent Tkinter window from actually showing up during tests:
        # We can either mock Tk itself or specific methods.
        # If SystemSageApp class directly inherits from tk.Tk, then self.app = SystemSageApp() will create a window.
        # Patching 'tkinter.Tk' can be broad. Let's try to be more targeted if possible,
        # or ensure all GUI interactions are through methods we can control/mock.
        # For now, assume SystemSageApp() can be instantiated, but we won't call mainloop.

        # If SystemSageApp's __init__ itself creates many UI elements that try to interact
        # with a non-existent Tk main loop or display, we might need to mock more.
        # A common approach is to mock methods that draw to screen or enter mainloop.

        # Let's try to create the app. If it fails, we'll need more setup mocking.
        # The __init__ method of SystemSageApp calls _setup_ui() which creates all widgets.
        # The __init__ method of SystemSageApp calls _setup_ui() which is now mocked.
        # Module-level MOCK_CTK_INIT_PATCHER handles super().__init__().
        # Decorators on setUp handle global customtkinter function calls and CTk methods called in SystemSageApp.__init__ before _setup_ui.

        # Start 'after' patcher
        self.after_patcher = patch.object(SystemSageApp, 'after', MagicMock())
        self.mock_after = self.after_patcher.start()
        
        self.app = SystemSageApp(cli_args=self.mock_args)
        self.app.mainloop = MagicMock() # Prevent mainloop

        # Since _setup_ui is mocked, we need to manually create and assign
        # the specific UI elements that are interacted with by the methods under test.
        self.app.ocl_profiles_table = MagicMock(spec=CTkTable) 
        self.app.ocl_profile_details_text = MagicMock(spec=customtkinter.CTkTextbox) 
        self.app.status_bar = MagicMock(spec=customtkinter.CTkLabel) 
        
        # Mock CTkInputDialog which is used by OCL methods like save_system_as_new_ocl_profile
        # We start it here and it will apply to all tests in this class.
        # Make sure to stop it in tearDown.
        self.mock_ctkinputdialog_patch = patch('customtkinter.CTkInputDialog', MagicMock())
        self.mock_ctkinputdialog = self.mock_ctkinputdialog_patch.start()


    def tearDown(self):
        """Clean up after each test."""
        self.mock_ctkinputdialog_patch.stop() # Stop the input dialog patch started in setUp
        self.after_patcher.stop() # Stop the after_patcher
        self.ocl_api_get_all_profiles_patcher.stop() # Stop the manually started patch

    def test_refresh_ocl_profiles_list_success(self):
        """Test refreshing OCL profiles list successfully."""
        sample_profiles = [
            {'id': 1, 'name': 'Profile 1', 'last_modified_date': '2023-01-01', 'description': 'Test Desc 1'},
            {'id': 2, 'name': 'Profile 2', 'last_modified_date': '2023-01-02', 'description': 'Test Desc 2'}
        ]
        self.mock_get_all_profiles.return_value = sample_profiles

        self.app.refresh_ocl_profiles_list()

        expected_table_values = [["ID", "Profile Name", "Last Modified"]]
        for p in sample_profiles:
            expected_table_values.append([str(p['id']), p['name'], p['last_modified_date']])
        
        self.app.ocl_profiles_table.update_values.assert_called_once_with(expected_table_values)
        self.app.status_bar.configure.assert_called_with(text="OCL Profiles refreshed.")
        self.assertIsNone(self.app.selected_ocl_profile_id)
        self.app.ocl_profile_details_text.configure.assert_any_call(state=customtkinter.NORMAL)
        self.app.ocl_profile_details_text.delete.assert_called_once_with("0.0", tk.END)
        self.app.ocl_profile_details_text.insert.assert_called_once_with("0.0", "Select a profile to view details.")
        self.app.ocl_profile_details_text.configure.assert_called_with(state=customtkinter.DISABLED)

    def test_refresh_ocl_profiles_list_empty(self):
        """Test refreshing OCL profiles list when no profiles are returned."""
        self.mock_get_all_profiles.return_value = []

        self.app.refresh_ocl_profiles_list()

        expected_table_values = [["ID", "Profile Name", "Last Modified"], ["No profiles found.", "", ""]]
        
        self.app.ocl_profiles_table.update_values.assert_called_once_with(expected_table_values)
        self.app.status_bar.configure.assert_called_with(text="OCL Profiles refreshed.")
        self.assertIsNone(self.app.selected_ocl_profile_id)

    @patch('systemsage_main.show_custom_messagebox') 
    def test_refresh_ocl_profiles_list_api_error(self, mock_show_custom_messagebox):
        """Test refreshing OCL profiles list when the API call raises an error."""
        self.mock_get_all_profiles.side_effect = Exception("API Failure")

        self.app.refresh_ocl_profiles_list()
        
        # Verify that the table was not updated with data beyond headers (or attempted to be cleared and left empty)
        # Depending on implementation, it might try to set headers first then fail.
        # For this test, we primarily care about error handling.
        # self.app.ocl_profiles_table.update_values.assert_called_once() # Or check it wasn't called with data

        mock_show_custom_messagebox.assert_called_once_with(self.app, "OCL Error", "Failed to refresh OCL profiles: API Failure", dialog_type="error")
        self.app.status_bar.configure.assert_called_with(text="OCL Profile refresh failed.")

    @patch('systemsage_main.logging.error')
    @patch('systemsage_main.show_custom_messagebox')
    def test_fetch_ocl_summary_method(self, mock_show_messagebox, mock_logging_error):
        """Test the _fetch_ocl_summary method for success and error cases."""
        # Success case
        sample_summary = [{'id': 1, 'name': 'Profile Alpha'}]
        self.mock_get_all_profiles.return_value = sample_summary
        self.mock_get_all_profiles.side_effect = None # Ensure no side effect from previous test

        summary = self.app._fetch_ocl_summary()
        self.mock_get_all_profiles.assert_called_once()
        self.assertEqual(summary, sample_summary)
        mock_show_messagebox.assert_not_called()
        mock_logging_error.assert_not_called()

        # Error case
        self.mock_get_all_profiles.reset_mock() # Reset call count etc.
        mock_show_messagebox.reset_mock()
        mock_logging_error.reset_mock()

        self.mock_get_all_profiles.side_effect = Exception("OCL API Down")
        summary_error = self.app._fetch_ocl_summary()
        
        self.mock_get_all_profiles.assert_called_once()
        self.assertEqual(summary_error, [])
        mock_show_messagebox.assert_called_once_with(self.app, "OCL Data Error", "Could not fetch OCL profile summary for report: OCL API Down", dialog_type="warning")
        mock_logging_error.assert_called_once()
        # Check that the error message contains "OCL API Down"
        args, _ = mock_logging_error.call_args
        self.assertIn("Error fetching OCL profiles summary: OCL API Down", args[0])


if __name__ == '__main__':
    unittest.main()
