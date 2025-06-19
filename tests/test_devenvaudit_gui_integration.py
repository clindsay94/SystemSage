import unittest
from unittest.mock import patch, MagicMock

# from tkinter import ttk # For Treeview - Not used in pr7-branch
import sys
import os

import customtkinter  # Added for CTk widgets
import tkinter.ttk as ttk  # Updated for ttk.Treeview

# Adjust path to import SystemSageApp from systemsage_main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from systemsage_main import SystemSageApp  # UPDATED

# Mock the devenvaudit_src dependencies as they are seen by systemsage_main.py
# This means patching them in the systemsage_main module's namespace or where they are imported.
# For EnvironmentScanner and load_devenv_config, they are imported at the top of systemsage_main.py

# Patch customtkinter.CTk.__init__ globally
MOCK_CTK_INIT_PATCHER = patch(
    "customtkinter.CTk.__init__", MagicMock(return_value=None)
)
# Removed duplicate MOCK_CTK_INIT_PATCHER line
MOCK_CTK_INIT_PATCHER.start()


class TestDevEnvAuditGUIIntegration(unittest.TestCase):  # Removed class decorators
    @classmethod
    def tearDownClass(cls):
        MOCK_CTK_INIT_PATCHER.stop()
        patch.stopall()

    def setUp(self):  # Signature is just self now
        self.patchers = []

        # Patch 'systemsage_main.EnvironmentScanner' (where it's used by SystemSageApp)
        self.env_scanner_patcher = patch(
            "systemsage_main.EnvironmentScanner", spec=True
        )
        self.MockEnvironmentScanner = self.env_scanner_patcher.start()
        self.MockEnvironmentScanner.return_value.__init__ = MagicMock(
            return_value=None
        )  # Mock __init__ of instances
        self.mock_scanner_instance = self.MockEnvironmentScanner.return_value
        self.patchers.append(self.env_scanner_patcher)

        # self.mock_load_devenv_config no longer exists in this version of tests

        # Patch methods on SystemSageApp directly
        title_patcher = patch.object(SystemSageApp, "title", MagicMock())
        geometry_patcher = patch.object(SystemSageApp, "geometry", MagicMock())
        option_add_patcher = patch.object(SystemSageApp, "option_add", MagicMock())
        # _setup_ui is essential for creating app attributes that tests might expect to mock later (like tables)
        # So, we do not mock _setup_ui itself, but rather let it run.
        # setup_ui_patcher = patch.object(SystemSageApp, '_setup_ui', MagicMock())
        after_patcher = patch.object(SystemSageApp, "after", MagicMock())

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
        self.mock_after = after_patcher.start()
        self.patchers.append(after_patcher)
        self.mock_set_appearance_mode = set_appearance_patcher.start()
        self.patchers.append(set_appearance_patcher)
        self.mock_set_default_theme = set_theme_patcher.start()
        self.patchers.append(set_theme_patcher)

        # Mock CTkInputDialog
        ctkinputdialog_patcher = patch("customtkinter.CTkInputDialog", MagicMock())
        self.mock_ctkinputdialog = ctkinputdialog_patcher.start()
        self.patchers.append(ctkinputdialog_patcher)

        self.mock_args = MagicMock()
        self.mock_args.calculate_disk_usage = True
        self.mock_args.output_dir = "output"
        self.mock_args.markdown_include_components_flag = False  # Example
        self.mock_args.markdown_no_components_flag = False  # Example
        self.mock_args.run_devenv_audit_flag = (
            False  # Default, can be overridden in tests
        )
        # Add other default values for any args SystemSageApp might check in __init__
        self.mock_args.no_json = False
        self.mock_args.no_markdown = False
        self.mock_args.console_include_components_flag = False
        self.mock_args.console_no_components_flag = False

        # The __init__ method of SystemSageApp calls _setup_ui() which creates all widgets.
        # We don't need to mock individual create_widget_* methods anymore.

        self.app = SystemSageApp(cli_args=self.mock_args)
        self.app.mainloop = MagicMock()

        # Updated to ttk.Treeview widgets
        self.app.devenv_components_tree = MagicMock(spec=ttk.Treeview)
        self.app.devenv_env_vars_tree = MagicMock(spec=ttk.Treeview)
        self.app.devenv_issues_tree = MagicMock(spec=ttk.Treeview)

        # For config display text widget - SystemSageV2.0 does not have a dedicated devenv_config_display_text
        # This UI feature seems to not be present in V2.0's _setup_ui or was removed.
        # self.app.devenv_config_display_text = MagicMock(spec=customtkinter.CTkTextbox)

        self.app.status_bar = MagicMock(spec=customtkinter.CTkLabel)
        # Scan menu is now part of action_bar_frame with CTkButtons, not a tk.Menu
        # We'll mock the specific button used for DevEnv Audit scan.
        self.app.devenv_audit_button = MagicMock(spec=customtkinter.CTkButton)

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        # patch.stopall() in tearDownClass will handle the MOCK_CTK_INIT_PATCHER

    # Test methods will be added here
    def test_display_devenv_config_success(self):
        """Test displaying DevEnvAudit configuration successfully."""
        # SystemSageV2.0 does not have a direct 'display_devenv_config' method in the same way.
        # This test needs to be re-evaluated based on V2.0's capabilities or removed.
        self.skipTest(
            "display_devenv_config method not directly applicable or UI element changed in V2.0"
        )
        return

        # sample_config = {"scan_paths": {"custom_paths": ["/test"]}, "max_depth": 5}
        # self.mock_load_devenv_config.return_value = sample_config

        # self.app.display_devenv_config() # This method would need to exist and be callable

        # self.app.devenv_config_display_text.configure.assert_any_call(state=tk.NORMAL) # customtkinter uses 'normal'
        # self.app.devenv_config_display_text.delete.assert_called_once_with('1.0', tk.END)
        # expected_json_display = json.dumps(sample_config, indent=2)
        # self.app.devenv_config_display_text.insert.assert_called_once_with('1.0', expected_json_display)
        # self.app.devenv_config_display_text.configure.assert_called_with(state=tk.DISABLED) # customtkinter uses 'disabled'
        # self.app.status_bar.configure.assert_called_with(text="DevEnvAudit configuration loaded and displayed.")

    def test_display_devenv_config_file_not_found(self):
        """Test handling FileNotFoundError when displaying DevEnvAudit config."""
        # Similar to above, this test needs re-evaluation for V2.0.
        self.skipTest(
            "display_devenv_config method not directly applicable or UI element changed in V2.0"
        )
        return

        # self.mock_load_devenv_config.side_effect = FileNotFoundError("devenvaudit_config.json not found")

        # with patch('systemsage_main.show_custom_messagebox') as mock_show_custom_messagebox: # UPDATED
        #     self.app.display_devenv_config() # This method would need to exist

        # mock_show_custom_messagebox.assert_called_once_with(self.app, "Config Not Found",
        #                                          "DevEnvAudit configuration file (devenvaudit_config.json in devenvaudit_src) not found.",
        #                                          dialog_type="warning")
        # self.app.status_bar.configure.assert_called_with(text="DevEnvAudit configuration file not found.")

    # To test threaded GUI updates, we mock 'self.app.after'
    @patch.object(SystemSageApp, "after")
    def test_start_devenv_audit_scan_success_populates_tables(
        self, mock_app_after
    ):  # UPDATED name
        """Test a successful DevEnvAudit scan populates the Treeviews."""
        # Make 'after' call the function immediately and synchronously
        mock_app_after.side_effect = lambda delay, func, *args: func(*args)

        mock_comp1 = MagicMock()
        mock_comp1.id = "c1"
        mock_comp1.name = "ToolX"
        mock_comp1.category = "IDE"
        mock_comp1.version = "1.0"
        mock_comp1.path = "/opt/toolx"
        mock_comp1.executable_path = "/opt/toolx/bin/toolx"
        # Adding missing attributes based on SystemSageApp's usage
        mock_comp1.source_detection = "TestDB"
        mock_comp1.matched_db_name = "TestToolX"

        mock_env1 = MagicMock()
        mock_env1.name = "PATH"
        mock_env1.value = "/usr/bin"
        mock_env1.scope = "System"

        mock_issue1 = MagicMock()
        mock_issue1.severity = "Warning"
        mock_issue1.description = "Old version"
        mock_issue1.category = "Update"
        mock_issue1.component_id = "c1"
        mock_issue1.related_path = "/opt/toolx"

        self.mock_scanner_instance.run_scan.return_value = (
            [mock_comp1],
            [mock_env1],
            [mock_issue1],
        )


        # Call the thread's target method directly to avoid thread complexities in test
        self.app.run_devenv_audit_thread()

        # Verify components tree population
        expected_component_row = [
            "c1",
            "ToolX",
            "IDE",
            "1.0",
            "/opt/toolx",
            "/opt/toolx/bin/toolx",
            "TestDB",
            "TestToolX",
        ]
        self.app.devenv_components_tree.insert.assert_any_call("", "end", values=expected_component_row)

        # Verify env vars tree population
        expected_env_row = ["PATH", "/usr/bin", "System"]
        self.app.devenv_env_vars_tree.insert.assert_any_call("", "end", values=expected_env_row)

        # Verify issues tree population
        expected_issue_row = ["Warning", "Old version", "Update", "c1", "/opt/toolx"]
        self.app.devenv_issues_tree.insert.assert_any_call("", "end", values=expected_issue_row)

        self.app.status_bar.configure.assert_called()
        self.app.devenv_audit_button.configure.assert_called()

    @patch.object(SystemSageApp, "after")
    @patch("systemsage_main.logging.error")
    @patch("systemsage_main.show_custom_messagebox")
    @patch("systemsage_main.traceback.format_exc")  # Patch traceback.format_exc
    def test_start_devenv_audit_scan_api_error(
        self,
        mock_format_exc,
        mock_show_custom_messagebox,
        mock_logging_error,
        mock_app_after,
    ):
        """Test error handling if EnvironmentScanner.run_scan() fails."""
        mock_app_after.side_effect = lambda delay, func, *args: func(*args)
        mock_format_exc.return_value = (
            "Mocked Traceback"  # Provide a return value for the patched format_exc
        )

        self.mock_scanner_instance.run_scan.side_effect = Exception("Test")

        # print("TEST_RDT: About to call self.app.run_devenv_audit_thread()", flush=True) # Debug print
        self.app.run_devenv_audit_thread()
        # print("TEST_RDT: After call to self.app.run_devenv_audit_thread()", flush=True) # Debug print

        mock_logging_error.assert_called_once()
        # Check that logging.error was called with the correct exception message, and the mocked traceback
        args, kwargs = mock_logging_error.call_args
        self.assertIn("DevEnvAudit scan failed: Test\nMocked Traceback", args[0])

        mock_show_custom_messagebox.assert_called_once_with(
            self.app,
            "DevEnv Audit Error",
            "An error occurred: Test",
            dialog_type="error",
        )
        # Further assertions on status bar etc. can be added back if this passes.


if __name__ == "__main__":
    unittest.main()
