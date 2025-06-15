import unittest
from unittest.mock import patch, mock_open
import json
import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# For DevEnvAudit modules:
from devenvaudit_src import config_manager as devenv_config_manager
from devenvaudit_src import scan_logic as devenv_scan_logic


class TestDevEnvAuditConfigLoading(unittest.TestCase):
    @patch("devenvaudit_src.config_manager.os.path.exists")
    @patch("devenvaudit_src.config_manager.open", new_callable=mock_open)
    @patch("devenvaudit_src.config_manager.os.makedirs")  # Mock makedirs
    def test_load_devenv_config_success(
        self, mock_makedirs, mock_file_open, mock_exists
    ):
        mock_exists.return_value = True
        sample_config_content = '{"scan_options": {"custom_paths": ["/test"]}}'
        # Configure the mock to simulate reading JSON content
        mock_file_open.return_value.read.return_value = sample_config_content

        # Patch json.load within the config_manager's scope
        with patch(
            "devenvaudit_src.config_manager.json.load",
            return_value=json.loads(sample_config_content),
        ) as mock_json_load:
            config = devenv_config_manager.load_config()

        self.assertEqual(config["scan_options"]["custom_paths"], ["/test"])
        mock_file_open.assert_called_with(
            devenv_config_manager.CONFIG_FILE_PATH, "r", encoding="utf-8"
        )
        mock_json_load.assert_called_once()
        mock_makedirs.assert_called_with(
            devenv_config_manager.CONFIG_DIR_PATH, exist_ok=True
        )

    @patch("devenvaudit_src.config_manager.os.path.exists", return_value=False)
    @patch(
        "devenvaudit_src.config_manager.open", new_callable=mock_open
    )  # To mock potential write
    @patch(
        "devenvaudit_src.config_manager.json.dump"
    )  # To mock json.dump during default config save
    @patch("devenvaudit_src.config_manager.os.makedirs")  # Mock makedirs
    def test_load_devenv_config_not_found_creates_default(
        self, mock_makedirs, mock_json_dump, mock_file_open_write, mock_exists
    ):
        # This test assumes load_config tries to save a default if not found
        # The _ensure_config_dir_exists is called first, then path.exists, then open for write

        # Simulate os.path.exists for _ensure_config_dir_exists (first call)
        # and then for load_config (second call)
        mock_exists.side_effect = [
            True,
            False,
        ]  # First call (dir exists), second call (file not found)

        config = devenv_config_manager.load_config()
        self.assertEqual(config, devenv_config_manager.DEFAULT_CONFIG)

        # Check if it attempted to save the default config
        # The open mock needs to handle the write call context manager
        mock_file_open_write.assert_any_call(
            devenv_config_manager.CONFIG_FILE_PATH, "w", encoding="utf-8"
        )

        # json.dump is called with the file object from open
        # We need to ensure mock_file_open_write() is used correctly for the context manager
        # This assertion might be tricky depending on how mock_open handles context managers.
        # A simpler way if mock_open().write is not directly usable:
        # Check if json.dump was called with the correct data.
        mock_json_dump.assert_called_with(
            devenv_config_manager.DEFAULT_CONFIG,
            mock_file_open_write.return_value.__enter__.return_value,
            indent=4,
        )
        mock_makedirs.assert_any_call(
            devenv_config_manager.CONFIG_DIR_PATH, exist_ok=True
        )


class TestDevEnvAuditScanLogicAssetLoading(unittest.TestCase):
    # Patch 'open' at the module level where scan_logic is defined.
    # This needs careful handling due to module-level loading in scan_logic.
    @patch("devenvaudit_src.scan_logic.open", new_callable=mock_open)
    def test_tools_db_loading_success(self, mock_file):
        # Set up the mock for the open call that loads TOOLS_DB_PATH
        tools_db_content = '[{"id": "test_tool", "name": "Test Tool"}]'

        # We need to ensure this mock is active when scan_logic is reloaded/imported.
        # The patch should apply to 'devenvaudit_src.scan_logic.open'

        # Mock json.load within scan_logic's scope
        with patch("devenvaudit_src.scan_logic.json.load") as mock_json_load:
            mock_json_load.return_value = json.loads(
                tools_db_content
            )  # Simulate successful JSON parsing

            # Configure the specific open call for TOOLS_DB_PATH
            # This is tricky because the path is constructed inside scan_logic.
            # A direct patch on scan_logic.open is better.
            # We'll assume the mock_file (patched scan_logic.open) is called correctly.
            # To ensure the mock is configured for the right file, we check the path later.
            # For now, just make sure it returns the content.
            mock_file.return_value.read.return_value = tools_db_content

            # Reload scan_logic to trigger module-level code execution with patches
            import importlib

            importlib.reload(devenv_scan_logic)

        # Verify TOOLS_DB content
        self.assertIsNotNone(devenv_scan_logic.TOOLS_DB, "TOOLS_DB should not be None")
        self.assertEqual(
            devenv_scan_logic.TOOLS_DB, [{"id": "test_tool", "name": "Test Tool"}]
        )

        # Verify open was called with the correct path (constructed in scan_logic)
        # This requires knowing the exact path string.
        expected_tools_db_path = os.path.join(
            os.path.dirname(devenv_scan_logic.__file__), "tools_database.json"
        )
        mock_file.assert_called_with(expected_tools_db_path, "r", encoding="utf-8")

    @patch.object(
        devenv_scan_logic.SoftwareCategorizer, "_load_database"
    )  # Mock method directly
    def test_software_categorizer_init_handles_db_load_failure(self, mock_load_db):
        mock_load_db.return_value = {}  # Simulate failed load
        categorizer = devenv_scan_logic.SoftwareCategorizer()
        self.assertEqual(categorizer.categorization_data, {})
        mock_load_db.assert_called_once()  # Ensure the mocked method was called


class TestEnvironmentScannerHelpers(unittest.TestCase):
    def setUp(self):
        # Create a dummy scanner instance, mocking config loading if it happens in __init__
        with (
            patch(
                "devenvaudit_src.scan_logic.load_config", return_value={}
            ),
            patch(
                "devenvaudit_src.scan_logic.get_scan_options", return_value={}
            ),
            patch("devenvaudit_src.scan_logic.SoftwareCategorizer"),
        ):
            self.scanner = devenv_scan_logic.EnvironmentScanner()

    @patch("subprocess.Popen")
    def test_get_version_from_command_success(self, mock_popen):
        mock_process = mock_popen.return_value
        # Ensure communicate returns bytes if text=False (default), or str if text=True
        # The code sets text=True, so stdout/stderr should be strings.

        mock_process.communicate.return_value = ("Python 3.9.1", "")

        mock_process.returncode = 0
        # Patch os.path.exists for the executable path check
        with patch("os.path.exists", return_value=True):
            version = self.scanner._get_version_from_command(
                "python", ["--version"], r"Python\s+([0-9\.]+)"
            )
        self.assertEqual(version, "3.9.1")

    @patch("subprocess.Popen")
    def test_get_version_from_command_timeout(self, mock_popen):
        # Simulate TimeoutExpired correctly
        mock_process = mock_popen.return_value
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="test", timeout=1
        )
        # Mock kill and subsequent communicate if needed by the logic

        mock_process.kill.return_value = None

        # The second communicate call after kill
        mock_process.communicate.return_value = ("", "TimeoutExpired after kill")

        with patch("os.path.exists", return_value=True):
            version = self.scanner._get_version_from_command("cmd", ["arg"], r"(.+)")
        self.assertIsNone(version)  # Or check for specific error logging/handling

    @patch.dict(
        os.environ, {"PATH": "/test/bin:/usr/bin"}, clear=True
    )  # clear=True ensures a clean PATH
    @patch("pathlib.Path.is_file")  # Patch is_file directly on Path objects
    @patch("pathlib.Path.resolve")  # Patch resolve
    @patch("os.access")  # os.access is still used
    def test_find_executable_in_path(
        self, mock_os_access, mock_path_resolve, mock_path_is_file
    ):
        # Scenario: exe exists and is executable

        # Configure mocks for Path objects
        # This requires knowing how Path objects are constructed and used.
        # If Path('/test/bin') / 'myexe' is called:

        def is_file_side_effect(path_obj):  # The path_obj is the Path instance
            return str(path_obj) == "/test/bin/myexe"

        mock_path_is_file.side_effect = is_file_side_effect

        # Make resolve return a new Path object with the resolved string, or just the string
        # The code uses str(exe_path.resolve()), so a string is fine.
        mock_path_resolve.side_effect = lambda: "/test/bin/myexe"

        mock_os_access.return_value = True  # os.access(exe_path, os.X_OK)

        # Clear cached found_executables for consistent test runs
        self.scanner.found_executables = {}
        found_path = self.scanner._find_executable_in_path("myexe")
        self.assertEqual(found_path, "/test/bin/myexe")

        # Scenario: exe not found
        mock_path_is_file.side_effect = lambda path_obj: False  # Reset side effect
        self.scanner.found_executables = {}  # Clear cache
        found_path_not = self.scanner._find_executable_in_path("another_exe")
        self.assertIsNone(found_path_not)


if __name__ == "__main__":
    unittest.main()
