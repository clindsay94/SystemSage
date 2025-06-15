import os
import platform
import subprocess
import re
import logging
from pathlib import Path
import json  # For parsing specific config files if needed

if platform.system() == "Windows":
    pass  # Keep for potential future use, though not used in current logic
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# Assuming config_manager.py and models.py are in the same directory or PYTHONPATH
from .config_manager import load_config

logger = logging.getLogger(__name__)


@dataclass
class DetectedComponent:
    """Holds information about a detected software component."""

    id: str
    name: str
    version: Optional[str] = None
    path: Optional[str] = None
    category: str = "Unknown"
    executable_path: Optional[str] = None
    details: dict = field(default_factory=dict)
    source_detection: Optional[str] = None  # Added field
    matched_db_name: Optional[str] = None  # Added field

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "category": self.category,
            "executable_path": self.executable_path,
            "details": self.details,
            "source_detection": self.source_detection,  # Added to dict
            "matched_db_name": self.matched_db_name,  # Added to dict
        }


@dataclass
class EnvironmentVariableInfo:
    """Holds information about a relevant environment variable."""

    name: str
    value: str
    scope: str  # e.g., "User", "System"

    def to_dict(self):
        return {"name": self.name, "value": self.value, "scope": self.scope}


@dataclass
class ScanIssue:
    """Represents an issue or potential problem identified during a scan."""

    severity: str  # e.g., "Error", "Warning", "Info"
    description: str
    category: str  # e.g., "Pathing", "Version", "Configuration"
    component_id: Optional[str] = None
    related_path: Optional[str] = None

    def to_dict(self):
        return {
            "severity": self.severity,
            "description": self.description,
            "category": self.category,
            "component_id": self.component_id,
            "related_path": self.related_path,
        }


# --- Constants ---
# Correct pathing assumes this script is in devenvaudit_src
SOFTWARE_CATEGORIZATION_DB_PATH = os.path.join(
    os.path.dirname(__file__), "software categorization database.json"
)
TOOLS_DB_PATH = os.path.join(os.path.dirname(__file__), "tools_database.json")

try:
    with open(TOOLS_DB_PATH, "r", encoding="utf-8") as f:
        TOOLS_DB = json.load(f)
    if not isinstance(TOOLS_DB, list):
        logger.error(
            f"TOOLS_DB loaded from {TOOLS_DB_PATH} is not a list. Defaulting to empty list."
        )
        TOOLS_DB = []
except FileNotFoundError:
    logger.error(
        f"Tools database file not found at {TOOLS_DB_PATH}. TOOLS_DB will be empty."
    )
    TOOLS_DB = []
except json.JSONDecodeError as e:
    logger.error(
        f"Error decoding JSON from {TOOLS_DB_PATH}: {e}. TOOLS_DB will be empty."
    )
    TOOLS_DB = []
except Exception as e:
    logger.error(
        f"Unexpected error loading {TOOLS_DB_PATH}: {e}. TOOLS_DB will be empty."
    )
    TOOLS_DB = []

if not TOOLS_DB:
    logger.warning(
        f"TOOLS_DB is empty after attempting to load from {TOOLS_DB_PATH}. Tool identification will be limited."
    )

SENSITIVE_ENV_VARS = [
    "API_KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASSWD",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
]


class SoftwareCategorizer:
    def __init__(self, categorization_data: Optional[Dict[str, Any]] = None):
        self.categorization_data = (
            categorization_data if categorization_data is not None else {}
        )
        if not self.categorization_data:
            logger.warning(
                "SoftwareCategorizer initialized with no categorization data. Categorization will be limited."
            )

    def categorize_component(
        self,
        component_name: str,
        component_path: Optional[str] = None,
        publisher: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Categorizes a component based on its name, path, and publisher."""
        if not self.categorization_data:
            return "Unknown", None

        comp_name_lower = component_name.lower() if component_name else ""
        exe_name_lower = self._get_executable_name(component_path)
        publisher_lower = publisher.lower() if publisher else ""

        if exe_name_lower:
            for category, entries in self.categorization_data.items():
                for entry in entries:
                    db_executables = [
                        e.lower() for e in entry.get("executables", []) if e
                    ]
                    if exe_name_lower in db_executables:
                        return category, entry.get("name")

        if comp_name_lower:
            for category, entries in self.categorization_data.items():
                for entry in entries:
                    db_entry_name_lower = entry.get("name", "").lower()
                    if db_entry_name_lower and db_entry_name_lower in comp_name_lower:
                        return category, entry.get("name")

                    keywords = [kw.lower() for kw in entry.get("keywords", [])]
                    if any(kw in comp_name_lower for kw in keywords):
                        return category, entry.get("name")
        if publisher_lower:
            for category, entries in self.categorization_data.items():
                for entry in entries:
                    db_publisher_lower = entry.get("publisher", "").lower()
                    if db_publisher_lower and db_publisher_lower in publisher_lower:
                        db_entry_name_lower = entry.get("name", "").lower()
                        keywords = [kw.lower() for kw in entry.get("keywords", [])]
                        if comp_name_lower:
                            if (
                                db_entry_name_lower
                                and db_entry_name_lower in comp_name_lower
                            ):
                                return category, entry.get("name")
                            if any(kw in comp_name_lower for kw in keywords):
                                return category, entry.get("name")
        return None, None

    def _get_executable_name(self, path_string: Optional[str]) -> Optional[str]:
        if not path_string:
            return None
        if any(
            path_string.lower().endswith(ext)
            for ext in [".exe", ".bat", ".cmd", ".sh", ".py", ".jar"]
        ):
            return os.path.basename(path_string).lower()

        match = re.match(
            r'("?)([^"]+\.(?:exe|bat|cmd|sh|py|jar))\1(?:,\d+)?',
            path_string,
            re.IGNORECASE,
        )
        if match:
            return os.path.basename(match.group(2)).lower()
        return None


class EnvironmentScanner:
    def __init__(self, progress_callback=None, status_callback=None):
        self.system = platform.system()
        self.config = load_config()  # Loads the main devenvaudit_config.json
        self.scan_options = self.config.get("scan_options", {})
        self.ignored_identifiers = set(
            self.config.get("ignored_tools_identifiers", [])
        )  # Corrected to use self.config and actual key
        self.detected_components: List[DetectedComponent] = []
        self.environment_variables: List[EnvironmentVariableInfo] = []
        self.issues: List[ScanIssue] = []
        self.found_executables: Dict[str, str] = {}  # Initialize found_executables

        # Assign callbacks
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        # Load tools_database.json and software_categorization_database.json directly
        # The TOOLS_DB_PATH loading block has been removed.

        try:
            with open(SOFTWARE_CATEGORIZATION_DB_PATH, "r", encoding="utf-8") as f_cat:
                self.software_categorization_db = json.load(f_cat)
            logger.info(
                f"Successfully loaded software categorization database from {SOFTWARE_CATEGORIZATION_DB_PATH}"
            )
        except FileNotFoundError:
            logger.error(
                f"Software categorization database file not found at {SOFTWARE_CATEGORIZATION_DB_PATH}. Categorization will be basic."
            )
            self.software_categorization_db = {}
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding JSON from {SOFTWARE_CATEGORIZATION_DB_PATH}: {e}. Categorization will be basic."
            )
            self.software_categorization_db = {}

        self.categorizer = SoftwareCategorizer(
            self.software_categorization_db
        )  # Pass loaded data to categorizer

    def _update_progress(self, current, total, message):
        if self.progress_callback:
            self.progress_callback(current, total, message)

    def _update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def _run_command(
        self, command_parts: List[str], timeout: int = 5
    ) -> Tuple[str, str, int]:
        process: Optional[subprocess.Popen] = None
        try:
            logger.debug(f"Running command: {' '.join(command_parts)}")
            process = subprocess.Popen(
                command_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stdout, stderr = process.communicate(timeout=timeout)
            return stdout, stderr, process.returncode
        except subprocess.TimeoutExpired:
            logger.warning(
                f"Command '{' '.join(command_parts)}' timed out after {timeout}s."
            )
            if process:
                process.kill()
                stdout, stderr_timeout = process.communicate()
                return stdout, f"TimeoutExpired: {stderr_timeout}", -1
            return (
                "",
                "TimeoutExpired: Process creation might have failed before timeout or was already handled.",
                -1,
            )
        except FileNotFoundError:
            logger.warning(f"Command not found: {command_parts[0]}")
            return "", "FileNotFoundError", -1
        except Exception as e:
            logger.error(f"Error running command '{' '.join(command_parts)}': {e}")
            return "", str(e), -1

    def _get_version_from_command(
        self, exe_path: str, version_args: List[str], version_regex_str: str
    ) -> Optional[str]:
        # FIX: Added a strict check to ensure we only try to execute valid program files.
        if self.system == "Windows" and not exe_path.lower().endswith(
            (".exe", ".bat", ".cmd", ".ps1")
        ):
            return None

        if not exe_path or not os.path.exists(exe_path):
            return None

        full_command = [exe_path] + version_args
        stdout, stderr, return_code = self._run_command(full_command)

        output_to_parse = ""
        if stdout:
            output_to_parse += stdout
        if stderr:
            output_to_parse += stderr

        if not output_to_parse.strip():
            logger.debug(f"No output from version command for {exe_path}")
            return None
        try:
            output_to_parse.encode("utf-8").decode("utf-8")
        except UnicodeEncodeError:
            try:
                output_to_parse = output_to_parse.encode("latin-1").decode(
                    "utf-8", errors="replace"
                )
                logger.debug(f"Had to re-decode output for {exe_path}")
            except Exception as e:
                logger.warning(f"Could not re-decode output for {exe_path}: {e}")

        match = re.search(
            version_regex_str, output_to_parse, re.MULTILINE | re.IGNORECASE
        )
        if match:
            if match.groups():
                version = match.group(1).strip()
                logger.info(f"Found version for {exe_path}: {version} using command.")
                return version
            else:
                logger.warning(
                    f"Version regex '{version_regex_str}' for {exe_path} matched but found no capture group in output: {output_to_parse[:200]}"
                )
        else:
            logger.debug(
                f"Version regex '{version_regex_str}' did not match for {exe_path}. Output: {output_to_parse[:200]}"
            )
        return None

    def _find_executable_in_path(self, exe_name: str) -> Optional[str]:
        if exe_name in self.found_executables:
            return self.found_executables[exe_name]

        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            if not path_dir:
                continue
            try:
                exe_path = Path(path_dir) / exe_name
                if exe_path.is_file() and os.access(exe_path, os.X_OK):
                    resolved_path = str(exe_path.resolve())
                    self.found_executables[exe_name] = resolved_path
                    return resolved_path
            except OSError:
                logger.warning(
                    f"Could not process PATH entry: {path_dir} when searching for {exe_name}"
                )
                continue
            except Exception as e:
                logger.error(f"Error checking executable {exe_name} in {path_dir}: {e}")
                continue
        return None

    def _find_executables_for_tool(self, tool_config: Dict[str, Any]) -> List[str]:
        exe_paths_found = set()
        current_system = platform.system()
        os_specific_executables = tool_config.get("executables", {}).get(
            current_system, []
        )
        if not os_specific_executables and current_system != "Windows":
            os_specific_executables = tool_config.get("executables", {}).get(
                "Linux", []
            )

        for exe_name in os_specific_executables:
            path_in_env = self._find_executable_in_path(exe_name)
            if path_in_env:
                exe_paths_found.add(os.path.realpath(path_in_env))

        common_install_paths = tool_config.get("install_paths", {}).get(
            current_system, []
        )
        for common_path_str in common_install_paths:
            try:
                common_path = Path(common_path_str)
                if common_path.is_file() and os.access(common_path, os.X_OK):
                    if common_path.name in os_specific_executables:
                        exe_paths_found.add(os.path.realpath(str(common_path)))
            except Exception as e:
                logger.warning(
                    f"Error processing common install path {common_path_str}: {e}"
                )
        return list(exe_paths_found)

    def _generate_component_id(
        self, name: str, version: Optional[str], path: Optional[str]
    ) -> str:
        name_slug = name.lower().replace(" ", "_").replace(".", "_")
        version_slug = version.replace(".", "_") if version else "unknown"
        path_slug = Path(path).name if path else "unknownpath"
        return f"{name_slug}_{version_slug}_{path_slug}"

    def _parse_gitconfig(self, file_path: str) -> Dict[str, str]:
        details = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                name_match = re.search(r"^\s*name\s*=\s*(.+)$", content, re.MULTILINE)
                email_match = re.search(r"^\s*email\s*=\s*(.+)$", content, re.MULTILINE)
                if name_match:
                    details["user.name"] = name_match.group(1).strip()
                if email_match:
                    details["user.email"] = email_match.group(1).strip()
        except Exception as e:
            logger.warning(f"Could not parse gitconfig {file_path}: {e}")
        return details

    def _get_tool_details(
        self,
        tool_config: Dict[str, Any],
        install_path: Optional[str],
        exe_path: Optional[str],
    ) -> Dict[str, Any]:
        details = {}
        if "config_files" in tool_config:
            for cf_info in tool_config["config_files"]:
                raw_path_str = cf_info["path"]
                conf_path: Optional[Path] = None
                if raw_path_str.startswith("~/"):
                    conf_path = Path(os.path.expanduser(raw_path_str))
                elif Path(raw_path_str).is_absolute():
                    conf_path = Path(raw_path_str)
                else:
                    base_dir_str = (
                        install_path
                        if install_path
                        else (str(Path(exe_path).parent) if exe_path else None)
                    )
                    if base_dir_str:
                        conf_path = Path(base_dir_str) / raw_path_str

                if conf_path and conf_path.exists() and conf_path.is_file():
                    parser_name = cf_info.get("parser")
                    if parser_name == "parse_gitconfig":
                        parsed_data = self._parse_gitconfig(str(conf_path))
                        for key in cf_info.get("keys", []):
                            if key in parsed_data:
                                details[f"{conf_path.name}:{key}"] = parsed_data[key]
                    else:
                        logger.warning(
                            f"Unknown parser '{parser_name}' for config file {conf_path}"
                        )
        return details

    def identify_tools(self):
        self._update_status("Identifying installed tools...")
        if not TOOLS_DB:
            logger.warning("TOOLS_DB is empty. Cannot identify specific tools.")
            self._update_progress(1, 1, "Tool identification skipped (TOOLS_DB empty).")
            return

        num_tools_defined = len(TOOLS_DB)
        for i, tool_cfg in enumerate(TOOLS_DB):
            tool_name = tool_cfg.get("name", "UnknownTool")
            self._update_status(f"Scanning for {tool_name}...")
            self._update_progress(i + 1, num_tools_defined, f"Scanning for {tool_name}")

            found_exe_paths = self._find_executables_for_tool(tool_cfg)

            if not found_exe_paths:
                logger.info(
                    f"No executables found for {tool_name} via PATH or common locations."
                )
                continue

            for exe_path_str in found_exe_paths:
                exe_path_obj = Path(exe_path_str)
                version = self._get_version_from_command(
                    str(exe_path_obj),
                    tool_cfg.get("version_args", ["--version"]),
                    tool_cfg.get("version_regex", r"([0-9]+\.[0-9]+(?:\.[0-9]+)?)"),
                )

                version = version if version else "Unknown"
                install_path = str(exe_path_obj.parent)
                component_id = self._generate_component_id(
                    tool_name, version, str(exe_path_obj)
                )

                if any(c.id == component_id for c in self.detected_components):
                    logger.debug(f"Skipping already detected instance: {component_id}")
                    continue
                if component_id in self.ignored_identifiers:
                    logger.info(f"Skipping ignored component: {component_id}")
                    continue

                details = self._get_tool_details(
                    tool_cfg, install_path, str(exe_path_obj)
                )
                related_env_vars_info = {}
                for env_var_name in tool_cfg.get("env_vars", []):
                    env_var_value = os.environ.get(env_var_name)
                    if env_var_value is not None:
                        if any(
                            s.lower() in env_var_name.lower()
                            for s in SENSITIVE_ENV_VARS
                        ):
                            related_env_vars_info[env_var_name] = "Present (sensitive)"
                        else:
                            related_env_vars_info[env_var_name] = env_var_value
                    else:
                        related_env_vars_info[env_var_name] = "Not set"
                if related_env_vars_info:
                    details["environment_variables"] = related_env_vars_info

                category, matched_db_name = self.categorizer.categorize_component(
                    tool_name, str(exe_path_obj)
                )

                component = DetectedComponent(
                    id=component_id,
                    name=tool_name,
                    category=category or tool_cfg.get("category", "Unknown"),
                    version=version,
                    path=install_path,
                    executable_path=str(exe_path_obj),
                    details=details,
                    source_detection=f"TOOLS_DB ({exe_path_obj.name})",
                    matched_db_name=matched_db_name,
                )
                self.detected_components.append(component)
                logger.info(
                    f"Detected via TOOLS_DB: {tool_name} {version} at {exe_path_obj}"
                )
        self._update_progress(
            num_tools_defined, num_tools_defined, "Tool identification complete."
        )

    def _analyze_env_var_for_issues(
        self, name: str, value: str, scope: str
    ) -> List[ScanIssue]:  # Changed IdentifiedIssue to ScanIssue
        """Analyzes a single environment variable for common issues."""
        issues: List[ScanIssue] = []  # Changed IdentifiedIssue to ScanIssue
        path_values = []

        # Check for multiple values in PATH-like variables
        if "path" in name.lower():
            path_values = [v.strip() for v in value.split(os.pathsep) if v.strip()]

        # Common checks for all environment variables
        # Issue: Empty or whitespace-only value
        if not value.strip():
            issues.append(
                ScanIssue(  # Changed IdentifiedIssue to ScanIssue
                    severity="Info",
                    description=f"Environment variable '{name}' is empty or contains only whitespace.",
                    category="Value",
                    component_id=None,
                    related_path=None,
                )
            )

        # Issue: Very long value (potentially suspicious)
        if len(value) > 255:
            issues.append(
                ScanIssue(  # Changed IdentifiedIssue to ScanIssue
                    severity="Warning",
                    description=f"Environment variable '{name}' has a very long value (>{255} characters).",
                    category="Length",
                    component_id=None,
                    related_path=None,
                )
            )

        # Issue: Invalid characters in the name
        if not re.match(r"^[A-Z0-9_]+$", name):
            issues.append(
                ScanIssue(  # Changed IdentifiedIssue to ScanIssue
                    severity="Warning",
                    description=f"Environment variable '{name}' contains invalid characters (only A-Z, 0-9, and _ are allowed).",
                    category="Format",
                    component_id=None,
                    related_path=None,
                )
            )

        # Issue: Path does not exist
        for p in path_values:
            if not os.path.exists(p):
                issues.append(
                    ScanIssue(  # Changed IdentifiedIssue to ScanIssue
                        severity="Warning",
                        description=f"Path '{p}' in environment variable '{name}' does not exist.",
                        category="Pathing",
                        component_id=None,
                        related_path=p,
                    )
                )

        # Issue: JAVA_HOME points to an invalid location (example check)
        if (
            "JAVA_HOME" in name
            and not os.path.exists(os.path.join(value, "bin", "java.exe"))
            and not os.path.exists(os.path.join(value, "bin", "java"))
        ):
            issues.append(
                ScanIssue(  # Changed IdentifiedIssue to ScanIssue
                    severity="Warning",
                    description=f"JAVA_HOME ('{value}') might not point to a valid JDK/JRE installation (missing bin/java).",
                    category="Configuration",
                    component_id=None,
                    related_path=None,
                )
            )

        # Check for potentially sensitive information (very basic example)
        # A more robust solution would involve regex patterns for keys, tokens, etc.
        if (
            any(s.lower() in name.lower() for s in SENSITIVE_ENV_VARS)
            and len(value) > 20
        ):  # Arbitrary length check
            issues.append(
                ScanIssue(  # Changed IdentifiedIssue to ScanIssue
                    severity="Warning",
                    description=f"Environment variable '{name}' might contain sensitive data.",
                    category="Security",
                    component_id=None,
                    related_path=None,
                )
            )

        return issues

    def collect_environment_variables(self):
        """
        Collects and analyzes environment variables.
        """
        self._update_status("Collecting environment variables...")
        self.environment_variables.clear()
        env_vars_dict = dict(os.environ)
        total_env_vars = len(env_vars_dict)
        processed_count = 0

        for name, value in env_vars_dict.items():
            processed_count += 1
            self._update_progress(
                processed_count,
                total_env_vars,
                f"Processing environment variable: {name}",
            )

            issues: List[ScanIssue] = []
            scope = "System/User"  # Default, difficult to determine exact scope without platform-specific calls

            # Check for sensitive information
            if any(keyword in name.upper() for keyword in SENSITIVE_ENV_VARS):
                issues.append(
                    ScanIssue(
                        severity="Warning",
                        description=f"Environment variable '{name}' might contain sensitive information.",
                        category="Security",
                        related_path=None,
                        component_id=None,
                    )
                )

            # Check PATH for invalid entries
            if name.upper() == "PATH":
                paths = value.split(os.pathsep)
                for i, path_entry in enumerate(paths):
                    if not path_entry:
                        continue  # Skip empty entries
                    # Check if path exists and is a directory
                    try:
                        if not os.path.exists(path_entry):
                            issues.append(
                                ScanIssue(
                                    severity="Warning",
                                    description=f"PATH entry '{path_entry}' does not exist.",
                                    category="Configuration",
                                    related_path=path_entry,
                                    component_id=None,
                                )
                            )
                        elif not os.path.isdir(path_entry):
                            issues.append(
                                ScanIssue(
                                    severity="Info",
                                    description=f"PATH entry '{path_entry}' exists but is not a directory.",
                                    category="Configuration",
                                    related_path=path_entry,
                                    component_id=None,
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Error checking PATH entry '{path_entry}': {e}")
                        issues.append(
                            ScanIssue(
                                severity="Warning",
                                description=f"Could not validate PATH entry '{path_entry}': {e}",
                                category="Configuration",
                                related_path=path_entry,
                                component_id=None,
                            )
                        )

            env_var_info = EnvironmentVariableInfo(name=name, value=value, scope=scope)
            self.environment_variables.append(env_var_info)
            # Analyze each variable for issues
            var_issues = self._analyze_env_var_for_issues(name, value, scope)
            self.issues.extend(var_issues)

            processed_count += 1
            if processed_count % 20 == 0:  # Update progress every 20 variables
                self._update_progress(
                    processed_count,
                    total_env_vars,
                    f"Processed {processed_count} environment variables.",
                )

        self._update_status("Environment variables collected.")

    def run_scan(self):
        """
        Executes the full environment scan.
        """
        self._update_status("Starting environment scan...")
        self.detected_components.clear()
        self.environment_variables.clear()
        self.issues.clear()
        self.found_executables.clear()

        # Phase 1: Identify known tools from the database
        self.identify_tools()

        # Phase 2: Analyze environment variables
        self.collect_environment_variables()

        # Phase 3: Cross-reference and analyze findings
        # self.cross_reference_and_analyze() # This phase is not yet implemented

        self._update_status("Scan complete.")
        logger.info("Full scan process finished.")
        # The main 'systemsage_main.py' seems to expect these three lists.
        # Let's ensure empty ones are returned for now for any logic not yet ported.
        return self.detected_components, self.environment_variables, self.issues
