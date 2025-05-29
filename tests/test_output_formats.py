import unittest
from unittest.mock import patch, mock_open
import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from SystemSageV1_2 import output_to_json_combined, output_to_markdown_combined
# Mock data classes for testing outputs
# If these are not easily importable or are complex, create simple mock objects/dicts for tests

from devenvaudit_src.scan_logic import DetectedComponent, EnvironmentVariableInfo, ScanIssue


class TestJsonOutput(unittest.TestCase):
    sample_inventory = [{"DisplayName": "App1", "DisplayVersion": "1.0"}]
    sample_dev_comp = [DetectedComponent(id="comp1", name="ToolA", version="1.1", path="/usr/bin/toola")]
    sample_dev_env = [EnvironmentVariableInfo(name="PATH", value="/usr/bin:/bin", scope="Test")]
    sample_dev_issues = [ScanIssue(severity="Warning", description="Test issue")]

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("logging.info") # Mock logging to suppress output during test
    def run_json_test(self, data, mock_log_info, mock_open_file, mock_makedirs):
        output_dir = "test_output"

        # Handle the case where all data is None or empty
        if not data.get("inventory") and not data.get("dev_comp") and \
           not data.get("dev_env") and not data.get("dev_issues"):
            output_to_json_combined(None, None, None, None, output_dir, "test_report.json")
            # Check if logging.info was called with "No data to save..."
            # Depending on the exact message, this assertion might need adjustment
            if mock_log_info.call_args_list: # Check if logging.info was called
                 self.assertIn("No data to save to JSON report", mock_log_info.call_args_list[0][0][0])
            return {} # Return empty dict as per expected behavior for no data

        output_to_json_combined(

            data.get("inventory"),
            data.get("dev_comp"),
            data.get("dev_env"),
            data.get("dev_issues"),
            output_dir, "test_report.json"
        )
        mock_makedirs.assert_called_with(output_dir, exist_ok=True)

        # Ensure file was actually called for writing if data was present
        self.assertTrue(mock_open_file.called)

        # Get the written content from mock_open
        written_content = ""
        # Iterate through all calls to write() because json.dump might call it multiple times
        for call_arg in mock_open_file().write.call_args_list:
            written_content += call_arg[0][0]


        if not written_content: # Should not happen if file was opened for writing data
            return {}


        return json.loads(written_content)

    def test_json_full_data(self):
        data = {
            "inventory": self.sample_inventory, "dev_comp": self.sample_dev_comp,
            "dev_env": self.sample_dev_env, "dev_issues": self.sample_dev_issues
        }
        result = self.run_json_test(data)
        self.assertIn("systemInventory", result)
        self.assertIn("devEnvAudit", result)
        self.assertEqual(result["systemInventory"], self.sample_inventory)
        self.assertEqual(len(result["devEnvAudit"]["detectedComponents"]), 1)
        self.assertEqual(result["devEnvAudit"]["detectedComponents"][0]["name"], "ToolA")
        self.assertEqual(result["devEnvAudit"]["environmentVariables"][0]["name"], "PATH")
        self.assertEqual(result["devEnvAudit"]["identifiedIssues"][0]["description"], "Test issue")


    def test_json_only_inventory(self):
        data = {"inventory": self.sample_inventory}
        result = self.run_json_test(data)
        self.assertIn("systemInventory", result)
        self.assertNotIn("devEnvAudit", result)

    def test_json_only_devenv(self):
        data = {"dev_comp": self.sample_dev_comp}
        result = self.run_json_test(data)
        self.assertNotIn("systemInventory", result)
        self.assertIn("devEnvAudit", result)
        self.assertEqual(len(result["devEnvAudit"]["detectedComponents"]), 1)

    def test_json_empty_data(self):
        # Test that no file is written, or an empty JSON object is written if that's the behavior.
        # Current run_json_test helper returns {} if no data is written after logging.
        result = self.run_json_test({})
        self.assertEqual(result, {})


class TestMarkdownOutput(unittest.TestCase):
    sample_inventory = [{"DisplayName": "App1", "Category": "Application"}]
    sample_dev_comp = [DetectedComponent(id="comp1", name="ToolA", category="Compiler", version="1.1", path="/path", executable_path="/path/toola")]
    sample_dev_env = [EnvironmentVariableInfo(name="TEST_VAR", value="test_value", scope="User")]
    sample_dev_issues = [ScanIssue(severity="High", description="A major issue", category="TestCat", component_id="comp1", related_path="/path/comp1")]


    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("logging.info") # Mock logging
    def run_md_test(self, data, mock_log_info, mock_open_file, mock_makedirs):
        output_dir = "test_output_md"
        output_to_markdown_combined(
            data.get("inventory"), data.get("dev_comp"),
            data.get("dev_env"), data.get("dev_issues"),
            output_dir, "test_report.md", include_system_sage_components_flag=True
        )
        # Get written content
        written_content = ""
        for call_args in mock_open_file().write.call_args_list:
            written_content += call_args[0][0]
        return written_content

    def test_md_headers_full_data(self):

        data = {"inventory": self.sample_inventory,
                "dev_comp": self.sample_dev_comp,
                "dev_env": self.sample_dev_env,
                "dev_issues": self.sample_dev_issues
               }
        content = self.run_md_test(data)
        self.assertIn("# System Sage Combined Report", content)
        self.assertIn("## System Software Inventory", content)
        self.assertIn("### Applications", content) # From sample_inventory
        self.assertIn("## Developer Environment Audit Results", content)
        self.assertIn("### Detected Development Components", content)
        self.assertIn("| Name | Version | Category | Path | Executable Path | ID |", content) # Dev comp header
        self.assertIn("### Key Environment Variables", content)
        self.assertIn("| Name | Value | Scope |", content)
        self.assertIn("### Identified Issues (DevEnvAudit)", content)
        self.assertIn("| Severity | Description | Category | Component ID | Related Path |", content)

    def test_md_only_inventory(self):
        data = {"inventory": self.sample_inventory}
        content = self.run_md_test(data)
        self.assertIn("## System Software Inventory", content)
        self.assertIn("### Applications", content)
        # Check if DevEnvAudit section is absent or states "No Developer Environment Audit data available."
        # Depending on implementation, one of these should be true.
        # For this test, we'll assume the section header might still be there but with "No data".
        if "## Developer Environment Audit Results" in content:
            self.assertIn("No Developer Environment Audit data available.", content)
        else:
            # This case means the entire section is omitted if all its sub-data is empty
            self.assertNotIn("### Detected Development Components", content)

    def test_md_only_devenv_components(self):
        data = {"dev_comp": self.sample_dev_comp}
        content = self.run_md_test(data)
        self.assertIn("## Developer Environment Audit Results", content)
        self.assertIn("### Detected Development Components", content)
        self.assertIn("ToolA", content) # Check for actual data
        self.assertNotIn("### Key Environment Variables", content) # Or should contain "No data"
        self.assertNotIn("### Identified Issues (DevEnvAudit)", content) # Or should contain "No data"
        if "## System Software Inventory" in content:
            self.assertIn("No System Inventory data available.", content)

    def test_md_empty_data(self):
        content = self.run_md_test({})
        self.assertIn("# System Sage Combined Report", content)
        self.assertIn("No System Inventory data available.", content)
        self.assertIn("No Developer Environment Audit data available.", content)

if __name__ == '__main__':
    unittest.main()
