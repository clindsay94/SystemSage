import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from devenvaudit_src.scan_logic import EnvironmentScanner

class TestStrictExecution(unittest.TestCase):
    def setUp(self):
        with patch("devenvaudit_src.scan_logic.load_config", return_value={}):
            with patch("devenvaudit_src.scan_logic.SoftwareCategorizer"):
                self.scanner = EnvironmentScanner()

    @patch("os.path.abspath")
    @patch("os.path.isfile")
    @patch("os.path.exists")
    @patch("os.access")
    def test_windows_valid_extension(self, mock_access, mock_exists, mock_isfile, mock_abspath):
        self.scanner.system = "Windows"
        mock_abspath.side_effect = lambda x: x
        mock_isfile.return_value = True
        mock_exists.return_value = True

        with patch.object(self.scanner, "_run_command") as mock_run:
            mock_run.return_value = ("v1.0", "", 0)
            version = self.scanner._get_version_from_command("test.exe", ["-v"], "(.*)")
            self.assertEqual(version, "v1.0")
            mock_run.assert_called_once()

    @patch("os.path.abspath")
    @patch("os.path.isfile")
    def test_windows_invalid_extension(self, mock_isfile, mock_abspath):
        self.scanner.system = "Windows"
        mock_abspath.side_effect = lambda x: x
        mock_isfile.return_value = True

        with patch.object(self.scanner, "_run_command") as mock_run:
            version = self.scanner._get_version_from_command("test.txt", ["-v"], "(.*)")
            self.assertIsNone(version)
            mock_run.assert_not_called()

    @patch("os.path.abspath")
    @patch("os.path.isfile")
    @patch("os.access")
    def test_linux_executable(self, mock_access, mock_isfile, mock_abspath):
        self.scanner.system = "Linux"
        mock_abspath.side_effect = lambda x: x
        mock_isfile.return_value = True
        mock_access.return_value = True # Executable

        with patch.object(self.scanner, "_run_command") as mock_run:
            mock_run.return_value = ("v1.0", "", 0)
            version = self.scanner._get_version_from_command("/usr/bin/test", ["-v"], "(.*)")
            self.assertEqual(version, "v1.0")
            mock_run.assert_called_once()

    @patch("os.path.abspath")
    @patch("os.path.isfile")
    @patch("os.path.exists")
    @patch("os.access")
    def test_linux_not_executable(self, mock_access, mock_exists, mock_isfile, mock_abspath):
        self.scanner.system = "Linux"
        mock_abspath.side_effect = lambda x: x
        mock_isfile.return_value = True
        mock_exists.return_value = True
        mock_access.return_value = False # Not executable

        with patch.object(self.scanner, "_run_command") as mock_run:
            version = self.scanner._get_version_from_command("/usr/bin/test", ["-v"], "(.*)")
            self.assertIsNone(version)
            mock_run.assert_not_called()

    @patch("os.path.abspath")
    @patch("os.path.isfile")
    def test_not_a_file(self, mock_isfile, mock_abspath):
        self.scanner.system = "Linux"
        mock_abspath.side_effect = lambda x: x
        mock_isfile.return_value = False # Directory or non-existent

        with patch.object(self.scanner, "_run_command") as mock_run:
            version = self.scanner._get_version_from_command("/usr/bin/dir", ["-v"], "(.*)")
            self.assertIsNone(version)
            mock_run.assert_not_called()

if __name__ == "__main__":
    unittest.main()
