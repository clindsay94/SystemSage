# ocl_module_src/bios_profile.py
# Author: System Sage
# Date: 06/15/2025
# Description: Defines the data structure for a detailed, hierarchical BIOS profile,
#              mirroring the structure of the ASRock BIOS profiler tool.

import uuid
import json
import os
from typing import Dict, Any, Optional, List

class Profile:
    """Represents a complete, hierarchical BIOS profile."""
    def __init__(self, name: str, description: str = "", profile_id: Optional[int] = None):
        self.id: Optional[int] = profile_id
        # Use a UUID for transient operations if no DB ID exists yet.
        self.transient_id: str = str(uuid.uuid4())
        self.name: str = name
        self.description: str = description
        self.settings: Dict[str, Dict[str, Any]] = {}

    def get_setting(self, section: str, setting_id: str) -> Any:
        """Retrieves a specific setting's value."""
        return self.settings.get(section, {}).get(setting_id, "")

    def set_setting(self, section: str, setting_id: str, value: Any):
        """Sets a specific setting's value."""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][setting_id] = value

    @staticmethod
    def from_flat_list(settings_list: list) -> Dict[str, Dict[str, Any]]:
        """Converts a flat list of settings from the DB into a hierarchical dict."""
        hierarchical_settings = {}
        if not isinstance(settings_list, list):
            return hierarchical_settings
            
        for setting in settings_list:
            category = setting.get('category')
            name = setting.get('setting_name')
            value = setting.get('setting_value')
            if category and name:
                if category not in hierarchical_settings:
                    hierarchical_settings[category] = {}
                hierarchical_settings[category][name] = value
        return hierarchical_settings

    @staticmethod
    def to_flat_list(hierarchical_settings: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts a hierarchical settings dict back to a flat list for the DB."""
        flat_list = []
        for category, settings in hierarchical_settings.items():
            for name, value in settings.items():
                flat_list.append({
                    "category": category,
                    "setting_name": name,
                    "setting_value": value,
                    "value_type": "str" 
                })
        return flat_list

# Define the mapping rules from keywords/prefixes in JSON keys to profile categories.
# Order is important: more specific patterns should come before general ones.
# The original JSON key's case will be preserved for the setting name itself.
BIOS_SETTING_CATEGORY_RULES = [
    # Most specific / high priority first (e.g., specific voltage names)
    ('cpu_vcore_volt', 'Voltage Configuration'), # Covers override, offset etc.
    ('cpu_gt_volt', 'Voltage Configuration'),
    ('cpu_sa_volt', 'Voltage Configuration'),
    ('cpu_io_volt', 'Voltage Configuration'),
    ('cpu_pll_volt', 'Voltage Configuration'),
    ('dram_ch_volt', 'Voltage Configuration'), # DRAM Channel A/B/C/D Voltage
    ('pch_volt', 'Voltage Configuration'), # PCH Core, PCH 1.8V etc.
    ('vpp_volt', 'Voltage Configuration'), # VPP_25V

    # General Voltages (if not caught by more specific rules above)
    ('vcore', 'Voltage Configuration'), 
    ('volt', 'Voltage Configuration'), # Broad, catches '...voltage', '..._volts'
    ('vcc', 'Voltage Configuration'), # vccio, vccsa, vccin_aux
    ('vdd', 'Voltage Configuration'), # vddq, vdd2
    ('vrm', 'Voltage Configuration'), # vrm_loadline, vrm_switching_freq
    ('llc', 'Voltage Configuration'), # load_line_calibration

    # CPU Specifics (after specific voltages)
    ('cpu_ratio', 'CPU Configuration'), # cpu_ratio_mode, cpu_ratio_apply
    ('cpu_bclk', 'CPU Configuration'), # cpu_bclk_oc_mode
    ('cpu_oc_mode', 'CPU Configuration'),
    ('core_ratio', 'CPU Configuration'), # core_ratio_limit_
    ('cache_ratio', 'CPU Configuration'), # also ring_ratio
    ('ring_ratio', 'CPU Configuration'),
    ('avx_offset', 'CPU Configuration'),
    ('avx_ratio_offset', 'CPU Configuration'), # avx_ratio_offset_for_avx512
    ('hyper_threading', 'Advanced CPU Configuration'),
    ('intel_speedstep', 'Advanced CPU Configuration'), # EIST
    ('intel_speed_shift', 'Advanced CPU Configuration'),
    ('c_state', 'Advanced CPU Configuration'), # c_state_control, c6_enable etc.
    ('turbo_mode', 'Advanced CPU Configuration'), # turbo_boost_enable
    ('cpu_thermal_monitor', 'Advanced CPU Configuration'),
    ('cpu_power_management', 'Advanced CPU Configuration'), # cpu_pkg_power_limit
    ('cpu_', 'CPU Configuration'), # General CPU catch-all

    # DRAM Specifics (after specific voltages)
    ('dram_freq', 'DRAM Configuration'), # dram_frequency
    ('dram_timing_', 'DRAM Configuration'), # dram_timing_control, dram_timing_tcl
    ('mem_timing_', 'DRAM Configuration'),
    ('dram_ref_clk', 'DRAM Configuration'), # dram_ref_clock_selection
    ('dram_command_rate', 'DRAM Configuration'), # cr1, cr2
    ('gear_down_mode', 'Advanced Memory Configuration'),
    ('power_down_enable', 'Advanced Memory Configuration'), # memory_power_down_mode
    ('memory_training_', 'Advanced Memory Configuration'), # memory_fast_boot, mrc_training_on_warm_boot
    ('mrc_fast_boot', 'Advanced Memory Configuration'),
    ('mem_interleaving', 'Advanced Memory Configuration'),
    ('dram_', 'DRAM Configuration'), # General dram_...
    ('memory_', 'DRAM Configuration'), # General memory_...

    # PCIE Configuration
    ('pcie_gen', 'PCIE Configuration'), # pcie_gen1_speed, pcie_link_speed_
    ('pcie_aspm', 'PCIE Configuration'), # pcie_dmi_aspm
    ('peg_port_', 'PCIE Configuration'), # peg_port_config, peg_max_link_speed
    ('pcie_', 'PCIE Configuration'), # General pcie_...

    # Storage (SATA, NVMe)
    ('sata_mode', 'SATA Configuration'), # ahci, raid, ide
    ('sata_hotplug_', 'SATA Configuration'),
    ('sata_aggressive_link_power', 'SATA Configuration'),
    ('sata_port_', 'SATA Configuration'), # sata_port_enable, sata_port_speed
    ('sata_', 'SATA Configuration'), # General sata_...
    ('nvme_firmware_update', 'NVMe Configuration'),
    ('nvme_sanitize', 'NVMe Configuration'),
    ('nvme_', 'NVMe Configuration'), # General nvme_...
    ('storage_oprom_policy', 'Storage Configuration'), # Storage Option ROM (UEFI/Legacy)
    ('raid_', 'Storage Configuration'), # raid_mode_enable

    # Onboard Devices, Network, USB, SuperIO
    ('onboard_lan_controller', 'Network Configuration'),
    ('onboard_wifi', 'Network Configuration'),
    ('onboard_bluetooth', 'Network Configuration'),
    ('onboard_audio_controller', 'Onboard Devices Configuration'),
    ('onboard_ieee1394', 'Onboard Devices Configuration'),
    ('onboard_', 'Onboard Devices Configuration'), # General onboard_...
    ('lan_option_rom', 'Network Configuration'),
    ('network_stack', 'Network Configuration'), # enable_ipv4_ipv6_network_stack
    ('network_', 'Network Configuration'), # General network_...
    ('usb_legacy_support', 'USB Configuration'),
    ('xhci_hand_off', 'USB Configuration'),
    ('usb_port_control', 'USB Configuration'), # usb_port_enable_disable
    ('usb_', 'USB Configuration'), # General usb_...
    ('superio_config_', 'Super IO Configuration'),
    ('serial_port_', 'Super IO Configuration'), # serial_port_address, serial_port_enable
    ('parallel_port_', 'Super IO Configuration'),

    # ACPI, CSM, Secure Boot
    ('acpi_sleep_state', 'ACPI Configuration'), # s3_enable, s4_s5_deep_sleep
    ('acpi_hpet_table', 'ACPI Configuration'),
    ('acpi_', 'ACPI Configuration'), # General acpi_...
    ('csm_launch_policy', 'CSM Configuration'), # launch_csm_enable
    ('csm_', 'CSM Configuration'), # General csm_...
    ('secure_boot_enable', 'Secure Boot Configuration'),
    ('secure_boot_mode', 'Secure Boot Configuration'), # standard, custom
    ('sb_key_management', 'Secure Boot Configuration'), # secure_boot_key_management
    ('sb_', 'Secure Boot Configuration'), # Short for Secure Boot

    # Boot Configuration
    ('fast_boot', 'Boot Configuration'),
    ('boot_logo_display', 'Boot Configuration'),
    ('boot_numlock_state', 'Boot Configuration'),
    ('boot_order_', 'Boot Configuration'), # boot_order_option_1
    ('boot_failure_guard_count', 'Boot Configuration'),
    ('boot_', 'Boot Configuration'), # General boot_...

    # Tool, Security (These might be less common as bulk settings from a generic export)
    ('bios_flash_', 'Tool'), 
    ('profile_slot_', 'Tool'), # e.g. profile_slot_load, profile_slot_save
    ('admin_password_status', 'Security'),
    ('user_password_status', 'Security'),
    ('password_', 'Security'), # General password_...
    
    # Overclocking Tweaker - if keys are explicitly prefixed, e.g., "oct_"
    ('oct_', 'Overclocking Tweaker'), 
]

DEFAULT_CATEGORY = "Imported Uncategorized"

def load_from_json_file(filepath: str) -> Optional[Profile]:
    """
    Loads a profile from a JSON file generated by the external HTML tool and
    attempts to map it to the hierarchical structure using predefined rules.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract profile name and description, using filename as fallback for name
        profile_name = data.pop('profileName', os.path.splitext(os.path.basename(filepath))[0])
        profile_description = data.pop('profileDescription', f"Imported from {os.path.basename(filepath)}")
        
        profile = Profile(name=profile_name, description=profile_description)
        
        imported_settings_count = 0
        uncategorized_settings_count = 0

        for key, value in data.items():
            # Preserve original key for setting_id, but match rules case-insensitively
            key_lower = key.lower()
            assigned_category = None
            
            for pattern, category_name in BIOS_SETTING_CATEGORY_RULES:
                if key_lower.startswith(pattern): # Match based on prefix
                    assigned_category = category_name
                    break 
            
            if assigned_category:
                profile.set_setting(assigned_category, key, value)
            else:
                profile.set_setting(DEFAULT_CATEGORY, key, value)
                uncategorized_settings_count += 1
            imported_settings_count += 1
        
        print(f"Profile '{profile.name}' loaded from '{os.path.basename(filepath)}'.")
        print(f"  Total settings processed: {imported_settings_count}.")
        if uncategorized_settings_count > 0:
            print(f"  Settings placed in '{DEFAULT_CATEGORY}': {uncategorized_settings_count}.")
            print(f"    Consider reviewing/updating BIOS_SETTING_CATEGORY_RULES in bios_profile.py if categories are incorrect.")
            # Optionally, list uncategorized keys for debugging:
            # if DEFAULT_CATEGORY in profile.settings:
            #     print(f"    Uncategorized keys: {list(profile.settings[DEFAULT_CATEGORY].keys())[:5]}")

        return profile
        
    except FileNotFoundError:
        print(f"Error: Profile JSON file not found at '{filepath}'.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{filepath}': {e}.")
        return None
    except Exception as e: # Catch any other unexpected errors during processing
        print(f"An unexpected error occurred while loading profile from JSON '{filepath}': {e}")
        return None
