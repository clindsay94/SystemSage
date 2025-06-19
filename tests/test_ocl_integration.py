import unittest
from unittest.mock import patch, MagicMock, call
import tkinter as tk
import sys
import os
import tkinter.ttk as ttk

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
from systemsage_main import SystemSageApp


class TestOCLIntegration(unittest.TestCase):
    def setUp(self):
        self.ctk_patcher = patch('customtkinter.CTk')
        self.MockCTk = self.ctk_patcher.start()

        self.patchers = []

        # Patch ocl_api and Treeview
        self.ocl_api_patcher = patch("systemsage_main.ocl_api")
        self.mock_ocl_api_module = self.ocl_api_patcher.start()
        self.patchers.append(self.ocl_api_patcher)

        self.treeview_patcher = patch("systemsage_main.ttk.Treeview")
        self.mock_treeview_class = self.treeview_patcher.start()
        self.patchers.append(self.treeview_patcher)

        self.mock_ocl_api = self.mock_ocl_api_module
        self.mock_get_all_profiles = self.mock_ocl_api.get_all_profiles
        self.mock_get_profile_details = self.mock_ocl_api.get_profile_details
        self.mock_create_new_profile = self.mock_ocl_api.create_new_profile
        self.mock_add_log_to_profile = self.mock_ocl_api.add_log_to_profile
        self.mock_update_existing_profile = (
            self.mock_ocl_api.update_existing_profile
        )

        # Patch other dependencies
        patch_definitions = [
            patch.object(SystemSageApp, "title", MagicMock()),
            patch.object(SystemSageApp, "geometry", MagicMock()),
            patch.object(SystemSageApp, "option_add", MagicMock()),
            patch("customtkinter.set_appearance_mode", MagicMock()),
            patch("customtkinter.set_default_color_theme", MagicMock()),
            patch("customtkinter.CTkInputDialog", MagicMock()),
            patch.object(SystemSageApp, "update_status_bar", MagicMock()),
        ]

        for p in patch_definitions:
            started_patch = p.start()
            self.patchers.append(p)
            if (
                hasattr(p, "target")
                and isinstance(p.target, str)
                and "CTkInputDialog" in p.target
            ):
                self.mock_ctkinputdialog = started_patch
            elif (
                hasattr(p, "attribute") and "update_status_bar" in p.attribute
            ):
                self.mock_update_status_bar = started_patch

        self.mock_args = MagicMock()
        self.mock_args.calculate_disk_usage = True
        self.mock_args.output_dir = "output"
        self.mock_args.markdown_include_components_flag = True
        self.mock_args.no_json = False
        self.mock_args.no_markdown = False
        self.mock_args.console_include_components_flag = False

        with patch.object(SystemSageApp, 'after', MagicMock(side_effect=lambda ms, func, *args: func(*args))):
            self.app = SystemSageApp(cli_args=self.mock_args)
        self.app.mainloop = MagicMock()

        # Since ttk.Treeview is patched, self.app.ocl_profiles_tree is a MagicMock.
        # We can assign it to ocl_tree_mock and use it for assertions.
        self.ocl_tree_mock = self.app.ocl_profiles_tree
        self.app.ocl_profile_details_text = MagicMock()

    def tearDown(self):
        self.ctk_patcher.stop()
        for patcher in self.patchers:
            patcher.stop()
        patch.stopall()

    def test_refresh_ocl_profiles_list_success(self):
        """Test refreshing OCL profiles list successfully."""
        sample_profiles = [
            {
                "id": 1,
                "name": "Profile Alpha",
                "last_modified_date": "2023-01-01",
            },
            {
                "id": 2,
                "name": "Profile Beta",
                "last_modified_date": "2023-01-02",
            },
        ]
        self.mock_get_all_profiles.return_value = sample_profiles

        self.app.refresh_ocl_profiles_list()

        self.ocl_tree_mock.delete.assert_called_with(*self.ocl_tree_mock.get_children())
        self.assertEqual(self.ocl_tree_mock.insert.call_count, 2)
        self.ocl_tree_mock.insert.assert_has_calls(
            [
                call(
                    "",
                    "end",
                    iid=1,
                    text="Profile Alpha",
                    values=("2023-01-01",),
                ),
                call(
                    "",
                    "end",
                    iid=2,
                    text="Profile Beta",
                    values=("2023-01-02",),
                ),
            ],
            any_order=True,
        )

    def test_on_ocl_profile_select_success(self):
        """Test selecting an OCL profile successfully."""
        profile_id = 1
        profile_details = {
            "id": profile_id,
            "name": "Profile Alpha",
            "description": "Test Description",
            "logs": [{"timestamp": "2023-01-01 12:00:00", "log_message": "Log 1"}],
        }
        self.mock_get_profile_details.return_value = profile_details

        # Mock the selection event
        mock_event = MagicMock()
        self.ocl_tree_mock.focus.return_value = profile_id
        self.app.on_ocl_profile_select(mock_event)

        self.mock_get_profile_details.assert_called_with(profile_id)
        self.app.ocl_profile_details_text.configure.assert_called()
        self.assertIn(
            "Profile Alpha",
            self.app.ocl_profile_details_text.configure.call_args[1]["text"],
        )


if __name__ == "__main__":
    unittest.main()
