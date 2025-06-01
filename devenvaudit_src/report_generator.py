"""Generates reports from scan results.
Takes raw data from scans and structures it for GUI display and export.
Handles formatting for TXT, MD, JSON, and HTML reports.
"""
import json
import logging
import html
from datetime import datetime
from typing import List, Dict, Any # Add typing imports

# Attempt to import data classes for type hinting
# These might still show as unresolved in Pylance if the root workspace/PYTHONPATH issue persists
from .scan_logic import DetectedComponent, EnvironmentVariableInfo, ScanIssue

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self,
                 detected_components: List[DetectedComponent],
                 environment_variables: List[EnvironmentVariableInfo],
                 issues: List[ScanIssue]):
        self.detected_components = sorted(detected_components, key=lambda x: (x.category, x.name, x.version))
        self.environment_variables = sorted(environment_variables, key=lambda x: x.name)
        self.issues = sorted(issues, key=lambda x: (x.severity, x.category, x.description))
        self.report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _format_component(self, component, format_type="txt"):
        """Formats a single component for different output types."""
        if format_type == "html":
            # Determine Executable/Command
            exe_command = os.path.basename(component.executable_path or component.path or "N/A")

            # Details Summary
            details_summary_parts = []
            if component.details:
                details_summary_parts.append(f"Update: {component.version} -> {component.update_info.get('latest_version', 'N/A')}")
            if component.issues:
                details_summary_parts.append(f"Issues: {len(component.issues)}")
            details_summary_str = "; ".join(details_summary_parts)
            if not details_summary_str:
                details_summary_str = "N/A"

            return f"""<tr>
  <td>{html.escape(str(component.name))}</td>
  <td>{html.escape(str(component.version))}</td>
  <td>{html.escape(str(component.category))}</td>
  <td><code>{html.escape(str(component.path))}</code></td>
  <td><code>{html.escape(exe_command)}</code></td>
  <td>{html.escape(details_summary_str)}</td>
</tr>"""

        lines = []
        name_version = f"{component.name} ({component.version})"
        if format_type == "md":
            lines.append(f"### {name_version}")
            lines.append(f"- **ID:** `{component.id}`")
            lines.append(f"- **Category:** {component.category}")
            lines.append(f"- **Path:** `{component.path}`")
            if component.executable_path and component.executable_path != component.path:
                lines.append(f"- **Executable:** `{component.executable_path}`")
        # Removed old HTML list formatting here
        else: # txt
            lines.append(f"Tool: {name_version}")
            lines.append(f"  ID: {component.id}")
            lines.append(f"  Category: {component.category}")
            lines.append(f"  Path: {component.path}")
            if component.executable_path and component.executable_path != component.path:
                lines.append(f"  Executable: {component.executable_path}")

        if component.details:
            # if format_type == "html": lines.append("<li><b>Details:</b><ul>") # Removed for table
            # else: lines.append(f"  Details:") # Keep for TXT/MD
            if format_type != "html": lines.append(f"  Details:")

            for key, value in component.details.items():
                if format_type == "md": lines.append(f"  - **{key}:** {value}")
                # elif format_type == "html": lines.append(f"<li><em>{html.escape(key)}:</em> {html.escape(str(value))}</li>") # Removed for table
                elif format_type != "html": lines.append(f"    {key}: {value}") # TXT
            # if format_type == "html": lines.append("</ul></li>") # Removed for table

        if component.update_info:
            ui = component.update_info
            status = "Update Available" if ui.get('is_update_available') else "Up-to-date"
            if ui.get('latest_version'):
                update_line = f"{status}: Installed {component.version} -> Latest {ui['latest_version']} (via {ui['package_manager_name']})"
                cmd_line = f"Update Command: `{ui['update_command']}`" if ui.get('update_command') else ""

                if format_type == "md":
                    lines.append(f"- **Update Status:** {update_line}")
                    if cmd_line: lines.append(f"  - {cmd_line}")
                # elif format_type == "html": # Removed for table
                #     lines.append(f"<li><b>Update Status:</b> {html.escape(update_line)}")
                #     if cmd_line: lines.append(f"<br/>&nbsp;&nbsp;<em>{html.escape(cmd_line)}</em>")
                #     lines.append("</li>")
                elif format_type != "html": # TXT
                    lines.append(f"  Update Status: {update_line}")
                    if cmd_line: lines.append(f"    {cmd_line}")

        if component.issues:
            # if format_type == "html": lines.append("<li><b>Issues:</b><ul>") # Removed for table
            # else: lines.append(f"  Issues:") # Keep for TXT/MD
            if format_type != "html": lines.append(f"  Issues:")
            for issue in component.issues: # issue is already a string or ScanIssue object
                desc = issue.description if hasattr(issue, 'description') else str(issue)
                sev = f" ({issue.severity})" if hasattr(issue, 'severity') else ""
                if format_type == "md": lines.append(f"  - *{desc}{sev}*")
                # elif format_type == "html": lines.append(f"<li><em>{html.escape(desc)}{html.escape(sev)}</em></li>") # Removed for table
                elif format_type != "html": lines.append(f"    - {desc}{sev}") # TXT
            # if format_type == "html": lines.append("</ul></li>") # Removed for table

        # if format_type == "html": lines.append("</ul>") # Removed for table
        if format_type != "html":
            return "\n".join(lines)
        # For HTML, the new method returns a full <tr> string, so this join is not needed for HTML.
        return "" # Should not be reached for HTML if logic is correct.


    def _format_env_var(self, env_var, format_type="txt"):
        lines = []
        val_display = env_var.value
        if len(val_display) > 200 and format_type != "json": # Truncate long values for readability
            val_display = val_display[:200] + "..."

        if format_type == "html":
            issues_str_parts = []
            if env_var.issues:
                for issue in env_var.issues:
                    desc = issue.description if hasattr(issue, 'description') else str(issue)
                    sev = f" ({issue.severity})" if hasattr(issue, 'severity') else ""
                    issues_str_parts.append(f"Issue:{html.escape(sev)} {html.escape(desc)}")
            issues_html_summary = "<br/>".join(issues_str_parts) if issues_str_parts else "OK"

            return f"""<tr>
  <td><code>{html.escape(env_var.name)}</code></td>
  <td><code>{html.escape(val_display)}</code></td>
  <td>{html.escape(env_var.scope)}</td>
  <td>{issues_html_summary}</td>
</tr>"""

        # For MD and TXT formats
        lines = []
        if format_type == "md":
            lines.append(f"- **`{html.escape(env_var.name)}`** (`{html.escape(env_var.scope)}`): `{html.escape(val_display)}`")
        else: # txt
            lines.append(f"{env_var.name} ({env_var.scope}): {val_display}")

        if env_var.issues:
            for issue in env_var.issues:
                desc = issue.description if hasattr(issue, 'description') else str(issue)
                sev = f" ({issue.severity})" if hasattr(issue, 'severity') else ""
                if format_type == "md": lines.append(f"  - *Issue:{html.escape(sev)} {html.escape(desc)}*")
                else: lines.append(f"  - Issue:{sev} {desc}")
        return "\n".join(lines)

    def _format_issue(self, issue, format_type="txt"):
        line = ""
        comp_info = f" (Component: {html.escape(str(issue.component_id))})" if issue.component_id else ""
        path_info = f" (Path: {html.escape(str(issue.related_path))})" if issue.related_path else ""

        if format_type == "html":
            related_info = html.escape(str(issue.component_id or issue.related_path or "N/A"))
            suggested_action = html.escape(str(issue.recommendation or "Refer to documentation/Investigate further"))

            # Apply class to severity cell for potential styling
            severity_class = f"severity-{html.escape(issue.severity.lower())}"

            return f"""<tr>
  <td>{html.escape(str(issue.category))}</td>
  <td>{html.escape(issue.description)}</td>
  <td>{related_info}</td>
  <td>{suggested_action}</td>
  <td class='{severity_class}'>{html.escape(str(issue.severity))}</td>
</tr>"""

        # For MD and TXT formats
        if format_type == "md":
            line = f"- **{html.escape(issue.severity)} ({html.escape(issue.category)}):** {html.escape(issue.description)}{comp_info}{path_info}"
            if issue.recommendation:
                line += f" (Suggestion: {html.escape(issue.recommendation)})"
        else: # txt
            line = f"- {issue.severity} ({issue.category}): {issue.description}{comp_info}{path_info}"
            if issue.recommendation:
                line += f" (Suggestion: {issue.recommendation})"
        return line

    def generate_report_data_for_gui(self):
        """Prepares data in a structured way suitable for the GUI."""
        # This can return the raw lists, and the GUI can format them.
        # Or, it can return pre-formatted strings if the GUI needs that.
        # For now, let's assume GUI will handle its own formatting from these objects.
        return {
            "report_time": self.report_time,
            "detected_components": [comp.to_dict() for comp in self.detected_components],
            "environment_variables": [ev.to_dict() for ev in self.environment_variables],
            "issues": [iss.to_dict() for iss in self.issues]
        }

    def export_to_txt(self, filepath):
        logger.info(f"Exporting report to TXT: {filepath}")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Developer Environment Audit Report\n")
                f.write(f"Generated: {self.report_time}\n")
                f.write("=" * 40 + "\n\n")

                f.write("Detected Tools & Versions\n")
                f.write("-" * 30 + "\n")
                if self.detected_components:
                    for comp in self.detected_components:
                        f.write(self._format_component(comp, "txt") + "\n\n")
                else:
                    f.write("No components detected.\n\n")

                f.write("Active Environment Variables\n")
                f.write("-" * 30 + "\n")
                if self.environment_variables:
                    for ev in self.environment_variables:
                        f.write(self._format_env_var(ev, "txt") + "\n")
                else:
                    f.write("No environment variables collected or to display.\n")
                f.write("\n")

                f.write("Identified Issues & Warnings\n")
                f.write("-" * 30 + "\n")
                if self.issues:
                    for issue in self.issues:
                        f.write(self._format_issue(issue, "txt") + "\n")
                else:
                    f.write("No issues identified.\n")
            logger.info(f"TXT report saved to {filepath}")
            return True
        except IOError as e:
            logger.error(f"Failed to write TXT report to {filepath}: {e}")
            return False

    def export_to_markdown(self, filepath):
        logger.info(f"Exporting report to Markdown: {filepath}")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Developer Environment Audit Report\n\n")
                f.write(f"**Generated:** {self.report_time}\n\n")
                f.write("---\n\n")

                f.write("## Detected Tools & Versions\n\n")
                if self.detected_components:
                    for comp in self.detected_components:
                        f.write(self._format_component(comp, "md") + "\n\n")
                else:
                    f.write("No components detected.\n\n")
                f.write("---\n\n")

                f.write("## Active Environment Variables\n\n")
                if self.environment_variables:
                    for ev in self.environment_variables:
                        f.write(self._format_env_var(ev, "md") + "\n")
                else:
                    f.write("No environment variables collected or to display.\n")
                f.write("\n---\n\n")

                f.write("## Identified Issues & Warnings\n\n")
                if self.issues:
                    for issue in self.issues:
                        f.write(self._format_issue(issue, "md") + "\n")
                else:
                    f.write("No issues identified.\n\n")
            logger.info(f"Markdown report saved to {filepath}")
            return True
        except IOError as e:
            logger.error(f"Failed to write Markdown report to {filepath}: {e}")
            return False

    def export_to_json(self, filepath):
        logger.info(f"Exporting report to JSON: {filepath}")
        report_data = self.generate_report_data_for_gui() # Use the same structure
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"JSON report saved to {filepath}")
            return True
        except (IOError, TypeError) as e: # TypeError for objects not serializable
            logger.error(f"Failed to write JSON report to {filepath}: {e}")
            return False

    def export_to_html(self, filepath):
        logger.info(f"Exporting report to HTML: {filepath}")
        # Define HTML template as a raw string literal
        html_template = f"""<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <title>Developer Environment Audit Report</title>
  <style>
    body {{ font-family: sans-serif; margin: 20px; line-height: 1.6; }}
    .container {{ max-width: 1000px; margin: auto; background: #f9f9f9; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
    h1, h2 {{ color: #333; }}
    h1 {{ text-align: center; }}
    h2 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 30px; }}
    /* ul {{ list-style-type: none; padding-left: 0; }} */ /* Not needed if all sections are tables */
    /* li {{ margin-bottom: 10px; }} */ /* Not needed if all sections are tables */
    code {{ background-color: #eef; padding: 2px 5px; border-radius: 4px; font-family: monospace; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
    th {{ background-color: #f0f0f0; }}
    tr:hover {{ background-color: #f5f5f5; }}
    /* Removed .issue class styling as issues are now in table rows */
    /* Specific styling for severity can be done via td classes if needed e.g. .severity-critical */
    .severity-critical {{ color: red; font-weight: bold; }}
    .severity-warning {{ color: orange; }}
    .severity-info {{ color: dodgerblue; }}
    .collapsible {{ background-color: #777; color: white; cursor: pointer; padding: 10px; width: 100%; border: none; text-align: left; outline: none; font-size: 1.1em; margin-top:10px; border-radius: 5px; }}
    .collapsible:hover {{ background-color: #555; }}
    .collapsible.active:after {{ content: "\\2212"; }} /* Minus sign */
    .collapsible:not(.active):after {{ content: '\\002B'; }} /* Plus sign */
    .collapsible:after {{ font-weight: bold; float: right; margin-left: 5px; }}
    .content {{ padding: 0 18px; max-height: 0; overflow: hidden; transition: max-height 0.2s ease-out; background-color: #f1f1f1; border-radius: 0 0 5px 5px; }}
    .timestamp {{ text-align: center; color: #777; margin-bottom: 20px; }}
  </style>
</head>
<body>
<div class='container'>
<h1>Developer Environment Audit Report</h1>
<p class='timestamp'>Generated: {html.escape(self.report_time)}</p>

<button type='button' class='collapsible active'>Detected Tools & Versions</button>
<div class='content' style='max-height: initial;'>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Version</th>
        <th>Category</th>
        <th>Path</th>
        <th>Executable/Command</th>
        <th>Details Summary</th>
      </tr>
    </thead>
    <tbody>
      {{components_section}}
    </tbody>
  </table>
</div>

<button type='button' class='collapsible'>Active Environment Variables</button>
<div class='content'>
  <table>
    <thead>
      <tr>
        <th>Variable Name</th>
        <th>Value</th>
        <th>Source</th>
        <th>Status/Notes</th>
      </tr>
    </thead>
    <tbody>
      {{env_vars_section}}
    </tbody>
  </table>
</div>

<button type='button' class='collapsible'>Identified Issues & Warnings</button>
<div class='content'>
  <table>
    <thead>
      <tr>
        <th>Issue Type</th>
        <th>Description</th>
        <th>Related Component/Variable</th>
        <th>Suggested Action</th>
        <th>Severity</th>
      </tr>
    </thead>
    <tbody>
      {{issues_section}}
    </tbody>
  </table>
</div>

<script>
  var coll = document.getElementsByClassName("collapsible");
  for (var i = 0; i < coll.length; i++) {{
    coll[i].addEventListener("click", function() {{
      this.classList.toggle("active");
      var content = this.nextElementSibling;
      if (content.style.maxHeight){{
        content.style.maxHeight = null;
      }} else {{
        // Ensure smooth animation for table by checking if parent is the one being animated.
        var parentContentDiv = this.nextElementSibling;
        if (parentContentDiv.classList.contains('content')) {{
            parentContentDiv.style.maxHeight = parentContentDiv.scrollHeight + "px";
        }} else {{
            // Fallback for other content types if any
            content.style.maxHeight = content.scrollHeight + "px";
        }}
      }}
    }});
  }}
</script>
</div>
</body>
</html>"""

        components_html = ""
        if self.detected_components:
            for comp in self.detected_components:
                components_html += self._format_component(comp, "html") + "\n" # Removed <hr/>
        else:
            components_html = "<tr><td colspan='6'>No components detected.</td></tr>\n"

        env_vars_html = ""
        if self.environment_variables:
            for ev in self.environment_variables:
                env_vars_html += self._format_env_var(ev, "html") + "\n"
        else:
            env_vars_html = "<tr><td colspan='4'>No environment variables collected or to display.</td></tr>\n"

        issues_html = ""
        if self.issues:
            for issue in self.issues:
                issues_html += self._format_issue(issue, "html") + "\n" # Removed div wrapper
        else:
            issues_html = "<tr><td colspan='5'>No issues identified.</td></tr>\n"

        final_html = html_template.replace("{{components_section}}", components_html)
        final_html = final_html.replace("{{env_vars_section}}", env_vars_html)
        final_html = final_html.replace("{{issues_section}}", issues_html)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_html)
            logger.info(f"HTML report saved to {filepath}")
            return True
        except IOError as e:
            logger.error(f"Failed to write HTML report to {filepath}: {e}")
            return False
        except Exception as e: # Catch any other unexpected error during HTML generation
            logger.error(f"An unexpected error occurred during HTML export: {e}", exc_info=True)
            return False


if __name__ == '__main__':
    # Ensure os is imported if running directly for os.path.basename used in _format_component
    import os
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create dummy data for testing
    # Assuming scan_logic.py is in the same directory or PYTHONPATH
    from scan_logic import DetectedComponent, EnvironmentVariableInfo, ScanIssue


    comps = [
        DetectedComponent(id="python_3.9_python.exe", name="Python", category="Language", version="3.9.7",
                          path="/usr/bin/python3.9", executable_path="/usr/bin/python3.9",
                          details={"Architecture": "64-bit", "Sub-details": {"More": "stuff", "EvenMore": "things"}},
                          update_info={"latest_version": "3.9.10", "package_manager_name": "apt",
                                       "update_command": "sudo apt upgrade python3", "is_update_available": True},
                          issues=[ScanIssue("Path not in system PATH", "Warning", "python_3.9_python.exe")]),
        DetectedComponent(id="git_2.30_git.exe", name="Git", category="VCS", version="2.30.1",
                          path="/usr/bin/git", executable_path="/usr/bin/git", details={"user.name": "Test User"})
    ]
    env_vars = [
        EnvironmentVariableInfo(name="PATH", value="/usr/bin:/bin:/usr/local/bin", issues=[
            ScanIssue("Entry '/usr/games' not found", "Warning", related_path="/usr/games")]),
        EnvironmentVariableInfo(name="JAVA_HOME", value="/opt/jdk-11", issues=[
            ScanIssue("Path /opt/jdk-11 does not exist", "Critical", related_path="/opt/jdk-11")]),
        EnvironmentVariableInfo(name="API_KEY_SECRET", value="supersecretvalue")
    ]
    issues = [
        ScanIssue("Global issue example", "Critical", category="System"),
        ScanIssue("Another warning", "Warning", component_id="python_3.9_python.exe", category="Configuration")
    ]

    reporter = ReportGenerator(comps, env_vars, issues)

    # Test exports
    output_dir = "test_reports"
    # import os # Already imported for __main__
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    reporter.export_to_txt(os.path.join(output_dir, "report.txt"))
    reporter.export_to_markdown(os.path.join(output_dir, "report.md"))
    reporter.export_to_json(os.path.join(output_dir, "report.json"))
    reporter.export_to_html(os.path.join(output_dir, "report.html"))

    print(f"Test reports generated in '{output_dir}' directory.")
