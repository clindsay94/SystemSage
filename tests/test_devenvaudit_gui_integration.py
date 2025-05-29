import unittest
from unittest.mock import patch, MagicMock, call
import tkinter as tk
from tkinter import ttk # For Treeview
import sys
import os
import json # For config display test

# Adjust path to import SystemSageApp from SystemSageV1.2.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from SystemSageV1_2 import SystemSageApp

# Mock the devenvaudit_src dependencies as they are seen by SystemSageV1_2.py
# This means patching them in the SystemSageV1_2 module's namespace or where they are imported.
# For EnvironmentScanner and load_devenv_config, they are imported at the top of SystemSageV1_2.py

@patch('SystemSageV1_2.load_devenv_config') # Mock config loaded by SystemSageApp for DevEnv
@patch('SystemSageV1_2.EnvironmentScanner') # Mock the scanner class at source of import
class TestDevEnvAuditGUIIntegration(unittest.TestCase):

    def setUp(self, MockEnvironmentScanner, mock_load_devenv_config_in_ss): # Order matters for decorators
        self.MockEnvironmentScanner = MockEnvironmentScanner
        self.mock_scanner_instance = self.MockEnvironmentScanner.return_value
        self.mock_load_devenv_config = mock_load_devenv_config_in_ss

        self.mock_args = MagicMock()
        self.mock_args.calculate_disk_usage = True
        self.mock_args.output_dir = "output"
        self.mock_args.markdown_include_components_flag = False # Example
        self.mock_args.markdown_no_components_flag = False    # Example
        self.mock_args.run_devenv_audit_flag = False # Default, can be overridden in tests
        # Add other default values for any args SystemSageApp might check in __init__
        self.mock_args.no_json = False
        self.mock_args.no_markdown = False
        self.mock_args.console_include_components_flag = False
        self.mock_args.console_no_components_flag = False


        # Mock methods that create main UI components called in SystemSageApp.__init__
        # to prevent actual Tk widget creation during test setup if they cause issues.
        # However, we need the devenv_tab and its children to be somewhat real for inspection.
        # The most robust way is to let __init__ run, then assign MagicMocks to specific treeviews.

        self.app = SystemSageApp(cli_args=self.mock_args)
        self.app.mainloop = MagicMock()

        # Replace actual UI elements with Mocks AFTER app initialization
        # This allows __init__ to create them, but tests interact with mocks.
        self.app.devenv_components_tree = MagicMock(spec=ttk.Treeview)
        self.app.devenv_env_vars_tree = MagicMock(spec=ttk.Treeview)
        self.app.devenv_issues_tree = MagicMock(spec=ttk.Treeview)

        # For config display text widget, it might be created in __init__ or a dedicated method.
        # Assuming it's an attribute after __init__ based on previous plans.
        # If it's created on-demand, this mock assignment needs to be more careful.
        # Based on Turn 60 plan, it's created in __init__
        self.app.devenv_config_display_text = MagicMock(spec=tk.Text)

        self.app.status_bar = MagicMock(spec=ttk.Label)
        self.app.scan_menu = MagicMock(spec=tk.Menu) # For disabling/enabling scan menu items

    def tearDown(self):
        if hasattr(self.app, 'destroy') and callable(self.app.destroy):
            try:
                self.app.destroy()
            except tk.TclError:
                pass
        patch.stopall() # Stops all active patches started with start()

    # Test methods will be added here
    def test_display_devenv_config_success(self):
        """Test displaying DevEnvAudit configuration successfully."""
        sample_config = {"scan_paths": {"custom_paths": ["/test"]}, "max_depth": 5}
        self.mock_load_devenv_config.return_value = sample_config # Mock the global function

        self.app.display_devenv_config()

        self.app.devenv_config_display_text.config.assert_any_call(state=tk.NORMAL)
        self.app.devenv_config_display_text.delete.assert_called_once_with('1.0', tk.END)
        expected_json_display = json.dumps(sample_config, indent=2)
        self.app.devenv_config_display_text.insert.assert_called_once_with('1.0', expected_json_display)
        self.app.devenv_config_display_text.config.assert_called_with(state=tk.DISABLED) # Check last call
        self.app.status_bar.config.assert_called_with(text="DevEnvAudit configuration loaded and displayed.")

    def test_display_devenv_config_file_not_found(self):
        """Test handling FileNotFoundError when displaying DevEnvAudit config."""
        self.mock_load_devenv_config.side_effect = FileNotFoundError("devenvaudit_config.json not found")

        with patch('SystemSageV1_2.messagebox.showwarning') as mock_showwarning:
            self.app.display_devenv_config()

        mock_showwarning.assert_called_once_with("Config Not Found",
                                                 "DevEnvAudit configuration file (devenvaudit_config.json in devenvaudit_src) not found.",
                                                 parent=self.app)
        self.app.status_bar.config.assert_called_with(text="DevEnvAudit configuration file not found.")

    # To test threaded GUI updates, we mock 'self.app.after'
    @patch.object(SystemSageApp, 'after')
    def test_start_devenv_audit_scan_success_populates_trees(self, mock_app_after):
        """Test a successful DevEnvAudit scan populates the Treeviews."""
        # Make 'after' call the function immediately and synchronously
        mock_app_after.side_effect = lambda delay, func, *args: func(*args)

        # Mock return data from scanner.run_scan()
        # Use MagicMocks for component, env_var, issue objects to allow attribute access
        mock_comp1 = MagicMock()
        mock_comp1.id = "c1"; mock_comp1.name="ToolX"; mock_comp1.category="IDE"; mock_comp1.version="1.0"; mock_comp1.path="/opt/toolx"; mock_comp1.executable_path="/opt/toolx/bin/toolx"

        mock_env1 = MagicMock()
        mock_env1.name="PATH"; mock_env1.value="/usr/bin"; mock_env1.scope="System"

        mock_issue1 = MagicMock()
        mock_issue1.severity="Warning"; mock_issue1.description="Old version"; mock_issue1.category="Update"; mock_issue1.component_id="c1"; mock_issue1.related_path="/opt/toolx"

        self.mock_scanner_instance.run_scan.return_value = ([mock_comp1], [mock_env1], [mock_issue1])

        # Mock get_children for all treeviews to simulate clearing
        self.app.devenv_components_tree.get_children.return_value = ['dummy_child_c']
        self.app.devenv_env_vars_tree.get_children.return_value = ['dummy_child_e']
        self.app.devenv_issues_tree.get_children.return_value = ['dummy_child_i']

        self.app.start_devenv_audit_scan()

        # Verify scan started
        self.app.status_bar.config.assert_any_call(text="Starting Developer Environment Audit...")
        self.app.scan_menu.entryconfig.assert_any_call("Run DevEnv Audit", state=tk.DISABLED)

        # Verify tree clearing
        self.app.devenv_components_tree.delete.assert_called_once_with('dummy_child_c')
        self.app.devenv_env_vars_tree.delete.assert_called_once_with('dummy_child_e')
        self.app.devenv_issues_tree.delete.assert_called_once_with('dummy_child_i')

        # Verify components tree population
        self.app.devenv_components_tree.insert.assert_called_once_with("", tk.END, values=(
            "c1", "ToolX", "IDE", "1.0", "/opt/toolx", "/opt/toolx/bin/toolx"
        ))
        # Verify env vars tree population
        self.app.devenv_env_vars_tree.insert.assert_called_once_with("", tk.END, values=(
            "PATH", "/usr/bin", "System"
        ))
        # Verify issues tree population
        self.app.devenv_issues_tree.insert.assert_called_once_with("", tk.END, values=(
            "Warning", "Old version", "Update", "c1", "/opt/toolx"
        ))

        # Verify final status update and menu re-enable (from finalize_devenv_scan)
        self.app.status_bar.config.assert_called_with(text="DevEnv Audit Complete. Found 1 components, 1 env vars, 1 issues.")
        self.app.scan_menu.entryconfig.assert_called_with("Run DevEnv Audit", state=tk.NORMAL)

    @patch.object(SystemSageApp, 'after')
    def test_start_devenv_audit_scan_api_error(self, mock_app_after):
        """Test error handling if EnvironmentScanner.run_scan() fails."""
        mock_app_after.side_effect = lambda delay, func, *args: func(*args) # Synchronous 'after'

        self.mock_scanner_instance.run_scan.side_effect = Exception("Major Scan Failure")

        with patch('SystemSageV1_2.messagebox.showerror') as mock_showerror:
            self.app.start_devenv_audit_scan()

        mock_showerror.assert_called_once_with("DevEnv Audit Error", "An error occurred during the Developer Environment Audit: Major Scan Failure")
        self.app.status_bar.config.assert_called_with(text="DevEnv Audit Failed.")
        self.app.scan_menu.entryconfig.assert_called_with("Run DevEnv Audit", state=tk.NORMAL)

if __name__ == '__main__':
    unittest.main()
