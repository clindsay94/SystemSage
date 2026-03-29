import unittest
from unittest.mock import patch, mock_open
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from devenvaudit_src import config_manager

class TestConfigManager(unittest.TestCase):
    @patch("devenvaudit_src.config_manager.load_config")
    @patch("devenvaudit_src.config_manager.save_config")
    def test_add_to_ignored_identifiers_new(self, mock_save, mock_load):
        # Initial config without the key
        mock_load.return_value = {}
        
        config_manager.add_to_ignored_identifiers("test_tool")
        
        # Verify save was called with the new identifier
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        self.assertIn("ignored_tools_identifiers", saved_config)
        self.assertEqual(saved_config["ignored_tools_identifiers"], ["test_tool"])

    @patch("devenvaudit_src.config_manager.load_config")
    @patch("devenvaudit_src.config_manager.save_config")
    def test_add_to_ignored_identifiers_duplicate(self, mock_save, mock_load):
        # Initial config with the identifier already present
        mock_load.return_value = {"ignored_tools_identifiers": ["test_tool"]}
        
        config_manager.add_to_ignored_identifiers("test_tool")
        
        # Verify save was NOT called
        mock_save.assert_not_called()

    @patch("devenvaudit_src.config_manager.load_config")
    def test_get_ignored_identifiers(self, mock_load):
        # Initial config with the identifier already present
        mock_load.return_value = {"ignored_tools_identifiers": ["test_tool"]}
        
        identifiers = config_manager.get_ignored_identifiers()
        
        self.assertEqual(identifiers, ["test_tool"])

    @patch("devenvaudit_src.config_manager.load_config")
    def test_get_ignored_identifiers_default(self, mock_load):
        # Initial config without the key
        mock_load.return_value = {}
        
        identifiers = config_manager.get_ignored_identifiers()
        
        # Should return the default value from DEFAULT_CONFIG
        self.assertEqual(identifiers, config_manager.DEFAULT_CONFIG["ignored_tools_identifiers"])

    @patch("devenvaudit_src.config_manager.load_config")
    @patch("devenvaudit_src.config_manager.save_config")
    def test_remove_from_ignored_identifiers_success(self, mock_save, mock_load):
        # Initial config with the identifier present
        mock_load.return_value = {"ignored_tools_identifiers": ["test_tool"]}
        
        config_manager.remove_from_ignored_identifiers("test_tool")
        
        # Verify save was called with the identifier removed
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        self.assertEqual(saved_config["ignored_tools_identifiers"], [])

    @patch("devenvaudit_src.config_manager.load_config")
    @patch("devenvaudit_src.config_manager.save_config")
    def test_remove_from_ignored_identifiers_not_found(self, mock_save, mock_load):
        # Initial config with the identifier not present
        mock_load.return_value = {"ignored_tools_identifiers": ["other_tool"]}
        
        config_manager.remove_from_ignored_identifiers("test_tool")
        
        # Verify save was NOT called
        mock_save.assert_not_called()

if __name__ == "__main__":
    unittest.main()
