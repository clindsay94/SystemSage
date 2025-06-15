import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk

# from tkinter import ttk # Not used in pr7-branch version
import sys
import os
# import json # Not used in pr7-branch version

import customtkinter  # Added for CTkTable and CTkTextbox
from CTkTable import CTkTable  # Added for CTkTable

# Adjust path to import SystemSageApp from systemsage_main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from systemsage_main import SystemSageApp  # UPDATED

# It's often good practice to mock the entire module that is external to the unit under test.
# We will use @patch decorators for specific test methods or the setUp method for `ocl_api`.

# Patch customtkinter.CTk.__init__ globally to prevent actual Tk window init
MOCK_CTK_INIT_PATCHER = patch(
    "customtkinter.CTk.__init__", MagicMock(return_value=None)
)
MOCK_CTK_INIT_PATCHER.start()


@patch(
    "systemsage_main.ocl_api"
)  # Mock the entire ocl_api module used by SystemSageApp
class TestOCLIntegration(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        MOCK_CTK_INIT_PATCHER.stop()
        patch.stopall()  # Stops all patches started with patch.start()

    def setUp(
        self, mock_ocl_api_module
    ):  # mock_ocl_api_module is injected by class decorator
        self.patchers = []  # For other patchers if any

        self.mock_ocl_api = mock_ocl_api_module
        # Configure specific methods if needed, e.g.
        self.mock_get_all_profiles = self.mock_ocl_api.get_all_profiles
        self.mock_get_profile_details = self.mock_ocl_api.get_profile_details
        self.mock_create_new_profile = self.mock_ocl_api.create_new_profile
        self.mock_add_log_to_profile = self.mock_ocl_api.add_log_to_profile
        self.mock_update_existing_profile = self.mock_ocl_api.update_existing_profile

        # Patch methods on SystemSageApp directly if they create UI elements or have side effects not needed for OCL tests
        # Many of these are for general app stability during testing, not specific to OCL tab.
        title_patcher = patch.object(SystemSageApp, "title", MagicMock())
        geometry_patcher = patch.object(SystemSageApp, "geometry", MagicMock())
        option_add_patcher = patch.object(SystemSageApp, "option_add", MagicMock())
        # _setup_ui is important, let it run to create .ocl_profiles_table etc.
        # setup_ui_patcher = patch.object(SystemSageApp, '_setup_ui', MagicMock())

        # Patch global customtkinter functions
        set_appearance_patcher = patch("customtkinter.set_appearance_mode", MagicMock())
        set_theme_patcher = patch("customtkinter.set_default_color_theme", MagicMock())

        self.mock_title = title_patcher.start()
        self.patchers.append(title_patcher)
        self.mock_geometry = geometry_patcher.start()
        self.patchers.append(geometry_patcher)
        self.mock_option_add = option_add_patcher.start()
        self.patchers.append(option_add_patcher)
        # self.mock_setup_ui = setup_ui_patcher.start() # Not mocking _setup_ui
        # self.patchers.append(setup_ui_patcher)
        self.mock_set_appearance_mode = set_appearance_patcher.start()
        self.patchers.append(set_appearance_patcher)
        self.mock_set_default_theme = set_theme_patcher.start()
        self.patchers.append(set_theme_patcher)

        # Mock CTkInputDialog as it's used in OCL operations
        self.ctkinputdialog_patch = patch("customtkinter.CTkInputDialog", MagicMock())
        self.mock_ctkinputdialog = self.ctkinputdialog_patch.start()
        self.patchers.append(self.ctkinputdialog_patch)

        # Mock CLI args if the app expects it
        self.mock_args = MagicMock()
        self.mock_args.calculate_disk_usage = True  # Default from SystemSageApp
        self.mock_args.output_dir = "output"  # Default from SystemSageApp
        self.mock_args.markdown_include_components_flag = True  # Default
        # Add any other args SystemSageApp might check in __init__ or related methods
        self.mock_args.no_json = False
        self.mock_args.no_markdown = False
        self.mock_args.console_include_components_flag = False

        # The __init__ method of SystemSageApp calls _setup_ui() which creates all widgets.
        # The __init__ method of SystemSageApp calls _setup_ui() which is now mocked.
        # Module-level MOCK_CTK_INIT_PATCHER handles super().__init__().

        # Start 'after' patcher
        self.after_patcher = patch.object(SystemSageApp, "after", MagicMock())
        self.mock_after = self.after_patcher.start()
        self.patchers.append(self.after_patcher)

        self.app = SystemSageApp(cli_args=self.mock_args)
        self.app.mainloop = MagicMock()  # Prevent actual mainloop call

        # Ensure essential OCL UI elements that are direct attributes of app exist as Mocks
        # These would normally be created in _setup_ui
        if not hasattr(self.app, "ocl_profiles_table"):
            self.app.ocl_profiles_table = MagicMock(spec=CTkTable)
        if not hasattr(self.app, "ocl_profile_details_text"):
            self.app.ocl_profile_details_text = MagicMock(spec=customtkinter.CTkTextbox)
        if not hasattr(self.app, "status_bar"):  # status_bar is general
            self.app.status_bar = MagicMock(spec=customtkinter.CTkLabel)

    def tearDown(self):
        """Clean up after each test."""
        for patcher in self.patchers:
            patcher.stop()
        # MOCK_CTK_INIT_PATCHER and class-level @patch for ocl_api are handled by @classmethod tearDownClass or unittest framework

    def test_refresh_ocl_profiles_list_success(self):
        """Test refreshing OCL profiles list successfully."""
        sample_profiles = [
            {"id": 1, "name": "Profile Alpha", "last_modified_date": "2023-01-01"},
            {"id": 2, "name": "Profile Beta", "last_modified_date": "2023-01-05"},
        ]
        self.mock_get_all_profiles.return_value = sample_profiles

        self.app.refresh_ocl_profiles_list()

        expected_table_values = [
            ["ID", "Profile Name", "Last Modified"],
            ["1", "Profile Alpha", "2023-01-01"],
            ["2", "Profile Beta", "2023-01-05"],
        ]
        self.app.ocl_profiles_table.update_values.assert_called_once_with(
            expected_table_values
        )
        self.app.status_bar.configure.assert_called_with(text="OCL Profiles refreshed.")
        self.assertIsNone(self.app.selected_ocl_profile_id)
        self.app.ocl_profile_details_text.configure.assert_any_call(
            state=customtkinter.NORMAL
        )
        self.app.ocl_profile_details_text.delete.assert_called_once_with("0.0", tk.END)
        self.app.ocl_profile_details_text.insert.assert_called_once_with(
            "0.0", "Select a profile to view details."
        )
        self.app.ocl_profile_details_text.configure.assert_called_with(
            state=customtkinter.DISABLED
        )

    def test_refresh_ocl_profiles_list_empty(self):
        """Test refreshing OCL profiles list when no profiles are returned."""
        self.mock_get_all_profiles.return_value = []
        self.app.refresh_ocl_profiles_list()
        expected_table_values = [
            ["ID", "Profile Name", "Last Modified"],
            ["No profiles found.", "", ""],
        ]
        self.app.ocl_profiles_table.update_values.assert_called_once_with(
            expected_table_values
        )
        self.assertIsNone(self.app.selected_ocl_profile_id)

    @patch("systemsage_main.show_custom_messagebox")
    def test_refresh_ocl_profiles_list_api_error(self, mock_show_custom_messagebox):
        """Test refreshing OCL profiles list when the API call raises an error."""
        self.mock_get_all_profiles.side_effect = Exception("OCL API Down")

        self.app.refresh_ocl_profiles_list()

        mock_show_custom_messagebox.assert_called_once()
        args, _ = mock_show_custom_messagebox.call_args
        self.assertEqual(args[0], self.app)  # Parent window
        self.assertEqual(args[1], "OCL Error")  # Title
        self.assertIn(
            "Failed to refresh OCL profiles: OCL API Down", args[2]
        )  # Message
        self.assertEqual(args[3], "error")  # Dialog type
        if self.app.status_bar:  # Check if status_bar was created
            self.app.status_bar.configure.assert_called_with(
                text="OCL Profile refresh failed."
            )


if __name__ == "__main__":
    unittest.main()
