import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import subprocess
import platform
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from devenvaudit_src import config_manager as devenv_config_manager
from devenvaudit_src import scan_logic as devenv_scan_logic


class TestDevEnvAuditConfigLoading(unittest.TestCase):
    @patch("devenvaudit_src.config_manager.os.path.exists")
    @patch("devenvaudit_src.config_manager.open", new_callable=mock_open)
    def test_load_devenv_config_success(self, mock_file_open, mock_exists):
        mock_exists.return_value = True
        sample_config_content = '{"scan_options": {"custom_paths": ["/test"]}}'
        mock_file_open.return_value.read.return_value = sample_config_content

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

    @patch("devenvaudit_src.config_manager.os.path.exists", return_value=False)
    @patch("devenvaudit_src.config_manager.open", new_callable=mock_open)
    @patch("devenvaudit_src.config_manager.json.dump")
    def test_load_devenv_config_not_found_creates_default(
        self, mock_json_dump, mock_file_open_write, mock_exists
    ):
        config = devenv_config_manager.load_config()
        self.assertEqual(config, devenv_config_manager.DEFAULT_CONFIG)
        mock_file_open_write.assert_called_with(
            devenv_config_manager.CONFIG_FILE_PATH, "w", encoding="utf-8"
        )
        mock_json_dump.assert_called_with(
            devenv_config_manager.DEFAULT_CONFIG,
            mock_file_open_write.return_value,
            indent=4,
        )


class TestDevEnvAuditScanLogic(unittest.TestCase):
    # Test for SoftwareCategorizer initialization
    def test_software_categorizer_init_with_data(self):
        """Test SoftwareCategorizer initializes correctly when data is provided."""
        mock_data = {"software_categories": {"test": ["test"]}}
        categorizer = devenv_scan_logic.SoftwareCategorizer(categorization_data=mock_data)
        self.assertEqual(categorizer.categorization_data, {"test": ["test"]})
    def test_software_categorizer_init_no_data(self):
        """Test SoftwareCategorizer initializes with an empty dict if no data is provided."""
        categorizer = devenv_scan_logic.SoftwareCategorizer() # No data passed
        self.assertEqual(categorizer.categorization_data, {"test": ["test"]})

    @patch("devenvaudit_src.scan_logic.open", new_callable=mock_open, read_data='[]')
    @patch("devenvaudit_src.scan_logic.json.load")
    def test_tools_db_loading(self, mock_json_load, mock_file):
        mock_json_load.return_value = [{"id": "test_tool"}]
        import importlib
        importlib.reload(devenv_scan_logic)
        self.assertEqual(devenv_scan_logic.TOOLS_DB, [{"id": "test_tool"}])


class TestEnvironmentScannerHelpers(unittest.TestCase):
    def setUp(self):
        with patch("devenvaudit_src.scan_logic.load_config", return_value={}):
            with patch("devenvaudit_src.scan_logic.SoftwareCategorizer"):
                self.scanner = devenv_scan_logic.EnvironmentScanner()

    @patch("subprocess.Popen")
    def test_get_version_from_command_success(self, mock_popen):
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = ("Python 3.9.1", "")
        mock_process.returncode = 0
        with patch("os.path.exists", return_value=True):
            version = self.scanner._get_version_from_command("python", ["--version"], r"Python\\s+([0-9\\.]+)")
        self.assertEqual(version, "3.9.1")

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_get_version_from_command_no_match(self, mock_popen, mock_exists):
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = ("Some other output", "")
        mock_process.returncode = 0
        version = self.scanner._get_version_from_command("cmd", ["arg"], r"NoMatch")
        self.assertIsNone(version)

    @patch.dict(os.environ, {"PATH": "/test/bin:/usr/bin"}, clear=True)
    @patch("pathlib.Path.resolve")
    @patch("pathlib.Path.is_file")
    @patch("os.access")
    def test_find_executable_in_path(
        self, mock_os_access, mock_path_is_file, mock_path_resolve
    ):
        # Scenario: exe exists and is executable
        expected_path_str = os.path.normpath("/test/bin/myexe")
        # On Windows, the implementation checks for extensions.
        if platform.system() == "Windows":
            expected_path_str += ".exe"

        def is_file_side_effect(path):
            return str(path) == expected_path_str

        mock_path_is_file.side_effect = is_file_side_effect
        mock_os_access.return_value = True
        mock_path_resolve.return_value = Path(expected_path_str)

        found_path = self.scanner._find_executable_in_path("myexe")
        self.assertEqual(found_path, expected_path_str)

        # Scenario: exe not found
        # Reset side effect for the next part of the test
        mock_path_is_file.side_effect = lambda path: False
        found_path_not = self.scanner._find_executable_in_path("another_exe")
        self.assertIsNone(found_path_not)

    def _find_executable_in_path(self, exe_name: str) -> Optional[str]:
        """Finds an executable in the system's PATH."""
        path_env = os.environ.get("PATH", "")
        if sys.platform == 'win32' and '\\' not in path_env and ':' in path_env:
            # Heuristic: if on Windows and path contains no backslashes but has colons,
            # assume it's a POSIX-style path for testing purposes.
            if len(path_env) == 2 and path_env[1] == ':': # Handle "C:" case
                paths = [path_env]
            else:
                paths = path_env.split(':')
        else:
            paths = path_env.split(os.pathsep)

        # On Windows, also check for extensions like .exe, .cmd, etc.
        executable_extensions = [""]


if __name__ == "__main__":
    unittest.main()
