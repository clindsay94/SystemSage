import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import customtkinter
import tkinter.ttk as ttk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from systemsage_main import SystemSageApp

class TestDevEnvAuditGUIIntegration(unittest.TestCase):

    def setUp(self):
        self.patchers = {
            'CTk': patch('customtkinter.CTk'),
            'EnvironmentScanner': patch("systemsage_main.EnvironmentScanner", autospec=True),
            '_setup_ui': patch('systemsage_main.SystemSageApp._setup_ui'),
            'perform_initial_scans': patch('systemsage_main.SystemSageApp.perform_initial_scans'),
            'after': patch.object(SystemSageApp, 'after', MagicMock(side_effect=lambda ms, func, *args: func(*args))),
            'Thread': patch('systemsage_main.Thread'),
            'update_status_bar': patch.object(SystemSageApp, 'update_status_bar', autospec=True),
            'show_custom_messagebox': patch('systemsage_main.show_custom_messagebox')
        }
        self.mocks = {name: patcher.start() for name, patcher in self.patchers.items()}

        # Configure the mock Thread to run synchronously
        mock_thread_class = self.mocks['Thread']
        def sync_thread_constructor(*args, **kwargs):
            target = kwargs.get('target')
            target_args = kwargs.get('args', ())
            target_kwargs = kwargs.get('kwargs', {})
            
            mock_thread_instance = MagicMock()
            if target:
                # When start() is called, it will execute the target function
                mock_thread_instance.start.side_effect = lambda: target(*target_args, **target_kwargs)
            return mock_thread_instance
        mock_thread_class.side_effect = sync_thread_constructor

        # Mock CLI args
        self.mock_args = MagicMock()
        self.mock_args.calculate_disk_usage = True
        self.mock_args.output_dir = "output"
        self.mock_args.markdown_include_components_flag = False
        self.mock_args.markdown_no_components_flag = False
        self.mock_args.run_devenv_audit_flag = False
        self.mock_args.no_json = False
        self.mock_args.no_markdown = False
        self.mock_args.console_include_components_flag = False
        self.mock_args.console_no_components_flag = False

        self.mock_scanner_instance = self.mocks['EnvironmentScanner'].return_value
        self.app = SystemSageApp(cli_args=self.mock_args)

        # Now, mock the UI elements that would have been created in _setup_ui
        self.app.devenv_components_tree = MagicMock(spec=ttk.Treeview)
        self.app.devenv_env_vars_tree = MagicMock(spec=ttk.Treeview)
        self.app.devenv_issues_tree = MagicMock(spec=ttk.Treeview)
        self.app.status_bar = MagicMock(spec=customtkinter.CTkLabel)
        self.app.devenv_audit_button = MagicMock(spec=customtkinter.CTkButton)
        self.app.mainloop = MagicMock()

    def tearDown(self):
        patch.stopall()

    def test_start_devenv_audit_scan_success_populates_tables(self):
        # Arrange
        self.mock_scanner_instance.run_scan.return_value = (
            [{"component": "Comp1", "details": "Detail1"}],
            [{"variable": "Var1", "value": "Val1"}],
            [{"issue": "Issue1", "description": "Desc1"}],
        )
        # Mock the update_devenv_audit_display to check calls
        self.app.update_devenv_audit_display = MagicMock()

        # Act
        self.app.start_devenv_audit_scan()

        # Assert
        self.app.update_devenv_audit_display.assert_called_once()
        self.mocks['update_status_bar'].assert_has_calls([
            call(self.app, 'Starting Developer Environment Audit...'),
            call(self.app, 'Developer Environment Audit complete.')
        ])

    def test_start_devenv_audit_scan_api_error(self):
        # Arrange
        self.mock_scanner_instance.run_scan.side_effect = Exception("API Error")
    
        # Act
        self.app.start_devenv_audit_scan()
    
        # Assert
        self.mocks['update_status_bar'].assert_has_calls([
            call(self.app, 'Starting Developer Environment Audit...'),
            call(self.app, 'Error during DevEnv audit: API Error')
        ])
        self.mocks['show_custom_messagebox'].assert_called_with(
            self.app, "DevEnv Audit Error", "Error during DevEnv audit: API Error", dialog_type="error"
        )


if __name__ == "__main__":
    unittest.main()
