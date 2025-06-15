import unittest
from unittest.mock import patch, mock_open
import json
import os

# Add this to allow importing SystemSageV1.2 directly for testing
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from systemsage_main import (
    format_size,
    is_likely_component,
    load_json_config,
)  # Import live ones too for some tests


class TestFormatSize(unittest.TestCase):
    def test_format_size_various(self):
        self.assertEqual(format_size(0, True), "0 B")  # type: ignore
        self.assertEqual(format_size(1023, True), "1023.00 B")  # type: ignore
        self.assertEqual(format_size(1024, True), "1.00 KB")  # type: ignore
        self.assertEqual(format_size(1024 * 1024 * 2.5, True), "2.50 MB")  # type: ignore
        self.assertEqual(format_size(0, False), "Not Calculated")  # type: ignore # Test 'Not Calculated'
        self.assertEqual(format_size(100, False), "Not Calculated")  # type: ignore # Test 'Not Calculated' with size
        self.assertEqual(format_size(-1, True), "N/A (Error)")  # type: ignore


class TestIsLikelyComponent(unittest.TestCase):
    # Using the globally loaded COMPONENT_KEYWORDS for these tests
    # This assumes COMPONENT_KEYWORDS is loaded correctly in SystemSageVV2.0.py
    # If SystemSageV2.0.py is not run before tests, COMPONENT_KEYWORDS might be the default one.
    # For more robust testing, one might need to mock the loading of COMPONENT_KEYWORDS
    # or ensure SystemSageVV2.0.COMPONENT_KEYWORDS is explicitly set/reloaded.
    def test_keywords(self):
        # Test with actual COMPONENT_KEYWORDS if they are loaded from file,
        # otherwise it will use DEFAULT_COMPONENT_KEYWORDS if file loading failed in SystemSageVV2.0.py
        self.assertTrue(is_likely_component("Some SDK", "Anycorp"))  # type: ignore # "sdk" is a keyword
        self.assertTrue(is_likely_component("Driver Update", "Anycorp"))  # type: ignore # "driver" is a keyword
        self.assertTrue(is_likely_component("Visual C++ Redistributable", "Microsoft"))  # type: ignore # "visual c++" and "redistributable"
        self.assertFalse(is_likely_component("My Application", "MyCompany"))  # type: ignore

    def test_heuristics(self):
        self.assertTrue(is_likely_component("{GUID-LIKE-STRING}", "Anycorp"))  # type: ignore
        self.assertTrue(is_likely_component("KB123456", "Microsoft"))  # type: ignore


class TestLoadJsonConfig(unittest.TestCase):
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_valid_json(self, mock_file_open, mock_path_exists):
        mock_path_exists.return_value = True
        # Configure the mock to simulate reading JSON content
        mock_file_open.return_value.read.return_value = '[{"key": "value"}]'

        # Since json.load is called on the file object, we need to ensure the file object itself
        # (mock_file_open.return_value) can be iterated by json.load or json.load is patched.
        # Patching json.load directly is often cleaner.
        with patch("json.load", return_value=[{"key": "value"}]) as mock_json_load:
            result = load_json_config.load_json_config("dummy.json", [])
            self.assertEqual(result, [{"key": "value"}])
            mock_file_open.assert_called_with("dummy.json", "r", encoding="utf-8")
            mock_json_load.assert_called_once()  # Ensure json.load was called

    @patch("os.path.exists", return_value=False)
    def test_file_not_found(self, mock_path_exists):
        default_data = ["default"]
        result = load_json_config("dummy.json", default_data)
        self.assertEqual(result, default_data)
        mock_path_exists.assert_called_with("dummy.json")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_json(self, mock_file_open, mock_path_exists):
        mock_file_open.return_value.read.return_value = "invalid json"
        # Patch json.load to simulate raising JSONDecodeError
        with patch(
            "json.load", side_effect=json.JSONDecodeError("err", "doc", 0)
        ) as mock_json_load:
            default_data = ["default_invalid"]
            result = load_json_config("dummy.json", default_data)
            self.assertEqual(result, default_data)
            mock_file_open.assert_called_with("dummy.json", "r", encoding="utf-8")
            mock_json_load.assert_called_once()


if __name__ == "__main__":
    unittest.main()
