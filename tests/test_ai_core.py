import unittest
import os
import time # Though not directly used in tests, model_loader uses it.
from unittest.mock import patch

# Add system_sage to sys.path to allow direct import of ai_core
# This assumes the tests are run from the root of the repository
import sys
# Correcting path to be relative to this test file's location to reach project root
# __file__ is tests/test_ai_core.py
# os.path.dirname(__file__) is tests/
# os.path.join(os.path.dirname(__file__), '..') is ./
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from system_sage.ai_core import model_loader
from system_sage.ai_core import file_manager_ai

class TestAICoreFunctions(unittest.TestCase):

    def setUp(self):
        """Ensure the dummy model flag file exists before each test."""
        self.model_flag_path = os.path.join(PROJECT_ROOT, "system_sage", "ai_core", "model_files", "gemma_model_files_exist.flag")
        os.makedirs(os.path.dirname(self.model_flag_path), exist_ok=True)
        with open(self.model_flag_path, 'w') as f:
            f.write("# Dummy flag for testing")


    def tearDown(self):
        """Clean up by ensuring the flag file is restored if a test removed it,
           or remove it if a test created it and it shouldn't persist (optional).
           For now, setUp handles ensuring it exists, so tearDown can be minimal
           unless a test specifically needs to clean up a file it created *that setUp doesn't manage*.
           Let's ensure it's restored if a test explicitly deletes it for its own purpose.
        """
        if not os.path.exists(self.model_flag_path):
            with open(self.model_flag_path, 'w') as f:
                f.write("# Dummy flag restored by tearDown")
        

    def test_check_model_availability_found(self):
        """Test that check_model_availability returns True when flag file exists."""
        self.assertTrue(model_loader.check_model_availability(), "Should return True when flag file exists.")

    def test_check_model_availability_not_found(self):
        """Test that check_model_availability returns False when flag file is missing."""
        if os.path.exists(self.model_flag_path):
            os.remove(self.model_flag_path)

        self.assertFalse(model_loader.check_model_availability(), "Should return False when flag file is missing.")

    def test_load_gemma_model_success(self):
        """Test successful model loading simulation when flag file exists."""
        self.assertTrue(model_loader.load_gemma_model(), "Should return True for successful simulated load.")

    def test_load_gemma_model_failure_due_to_availability(self):
        """Test model loading failure when flag file is missing."""
        if os.path.exists(self.model_flag_path):
            os.remove(self.model_flag_path)
        
        self.assertFalse(model_loader.load_gemma_model(), "Should return False when model is not available.")

    def test_analyze_system_data_returns_string(self):
        """Test that analyze_system_data returns a non-empty string."""
        dummy_data = {"test_key": "test_value"}
        response = model_loader.analyze_system_data(dummy_data)
        self.assertIsInstance(response, str, "Response should be a string.")
        self.assertTrue(len(response) > 0, "Response string should not be empty.")

    def test_get_file_management_suggestions_returns_list_of_dicts(self):
        """Test that get_file_management_suggestions returns a list of suggestion dicts."""
        suggestions = file_manager_ai.get_file_management_suggestions([])
        self.assertIsInstance(suggestions, list, "Should return a list.")
        
        self.assertTrue(len(suggestions) > 0, "Should return a non-empty list of suggestions.")
        
        if suggestions: 
            first_suggestion = suggestions[0]
            self.assertIsInstance(first_suggestion, dict, "Each suggestion should be a dictionary.")
            self.assertIn('suggestion', first_suggestion, "Suggestion dict should have a 'suggestion' key.")
            self.assertIn('action', first_suggestion, "Suggestion dict should have an 'action' key.")
            self.assertTrue(len(first_suggestion['suggestion']) > 0)
            self.assertTrue(len(first_suggestion['action']) > 0)

if __name__ == '__main__':
    unittest.main()
```
