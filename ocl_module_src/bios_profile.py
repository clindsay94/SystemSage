"""
This module defines the data structures for BIOS profiles.
"""
import json
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Optional, List, Dict, Any, Type, TypeVar

# Helper function to create a list of a specific dataclass type
def _create_list(factory, count):
    return [factory() for _ in range(count)]

# Sub-structures for complex settings like Curve Optimizer and Fan Control

@dataclass
class PerCoreCurveOptimizer:
    sign: str = "Negative"
    magnitude: int = 0

@dataclass
class CurveShaperSetting:
    enable: str = "Auto"
    sign: str = "Positive"
    magnitude: int = 0

@dataclass
class FanSpeedPoint:
    temperature: int = 40
    duty_cycle: int = 20

# Main Sections

@dataclass
class MainSettings:
    bios_version: str = ""
    processor_type: str = ""
    max_speed: str = ""
    total_memory: str = ""
    dram_a1: str = "Not Present"
    dram_a2: str = "Not Present"
    dram_b1: str = "Not Present"
    dram_b2: str = "Not Present"
    notes: str = ""

@dataclass
class DramTimingSettings:
    tcl: int = 0
    trcdrd: int = 0
    trp: int = 0
    tras: int = 0
    trc: int = 0
    twr: int = 0
    trefi: int = 0
    trfc1: int = 0
    trfc2: int = 0
    trfcsb: int = 0
    trtp: int = 0
    trrd_l: int = 0
    trrd_s: int = 0
    tfaw: int = 0
    twtr_l: int = 0
    twtr_s: int = 0
    trdrd_scl: int = 0
    trdrd_sc: int = 0
    trdrd_sd: int = 0
    trdrd_dd: int = 0
    twrwr_scl: int = 0
    twrwr_sc: int = 0
    twrwr_sd: int = 0
    twrwr_dd: int = 0
    twrrd: int = 0
    trdwr: int = 0

@dataclass
class DramBusControlSettings:
    rtt_nom_rd: str = "Auto"
    rtt_nom_wr: str = "Auto"
    rtt_wr: str = "Auto"
    rtt_park: str = "Auto"
    dqs_rtt_park: str = "Auto"
    dq_drive_strength: str = ""
    proc_odt_impedance: str = ""
    proc_dq_drive_strength: str = ""
    proc_ca_drive_strength: str = ""

@dataclass
class ExternalVoltageSettings:
    vddcr_cpu_voltage_mode: str = "Auto"
    vddcr_cpu_voltage_value: str = ""
    vddcr_cpu_llc: str = "Auto"
    vddcr_soc_voltage_mode: str = "Auto"
    vddcr_soc_voltage_value: str = ""
    vddcr_soc_llc: str = "Auto"
    vdd_misc_voltage_ext_mode: str = "Auto"
    vdd_misc_voltage_ext_value: str = ""
    vdd_misc_s5_voltage: str = "Auto"
    pch1_105v_voltage: str = "Auto"
    pch2_105v_voltage: str = "Auto"
    pch_1_8v_voltage: str = "Auto"

@dataclass
class OcTweakerSettings:
    gaming_mode: str = "Disabled"
    zen5_gaming_optimizations: str = "Enabled"
    tdp_to_105w: str = "Disabled"
    performance_boost: str = "Auto"
    performance_preset: str = "Auto"
    platform_thermal_throttle_limit_tjmax: int = 90
    cpu_overclocking: str = "Auto"
    gfx_overclocking: str = "Auto"
    dram_frequency: str = "6000"
    memory_context_restore: str = "Enabled"
    vddio_voltage: str = ""
    dram_vdd_voltage: str = ""
    dram_vddq_voltage: str = ""
    dram_vpp_voltage: str = ""
    infinity_fabric_frequency: str = "2133"
    uclk_div_mode: str = "UCLK=MEMCLK"
    oc_vdd_soc_direct_mode: str = "Auto"
    oc_vdd_soc_direct_value: str = ""
    oc_vdd_misc_direct_mode: str = "Auto"
    oc_vdd_misc_direct_value: str = ""
    oc_vddg_ccd_voltage_mode: str = "Auto"
    oc_vddg_ccd_voltage_value: str = ""
    oc_vddg_iod_voltage_mode: str = "Auto"
    oc_vddg_iod_voltage_value: str = ""
    oc_vddp_voltage_mode: str = "Auto"
    oc_vddp_voltage_value: str = ""
    oc_bus_speed_mode: str = "Auto"
    oc_bus_speed_value: float = 100.00
    dram_profile_setting: str = ""
    dram_performance_mode: str = "AMD AGESA Default"
    dram_timings: DramTimingSettings = field(default_factory=DramTimingSettings)
    dram_bus_control: DramBusControlSettings = field(default_factory=DramBusControlSettings)
    external_voltages: ExternalVoltageSettings = field(default_factory=ExternalVoltageSettings)
    notes: str = ""

@dataclass
class AdvancedCpuConfig:
    amd_ftpm_switch: str = "AMD CPU fTPM"
    pss_support: str = "Enabled"
    nx_mode: str = "Enabled"
    smt_mode: str = "Auto"
    adv_avx512: str = "Enabled"

@dataclass
class AdvancedAcpiConfig:
    suspend_to_ram: str = "Disabled"
    restore_on_ac_power_loss: str = "Power Off"
    deep_sleep: str = "Disabled"
    usb_device_power_on: str = "Disabled"
    usb_power_delivery_s5: str = "Enabled"
    pcie_devices_power_on: str = "Enabled"
    rtc_alarm_power_on: str = "Disabled"

@dataclass
class AdvancedStorageConfig:
    sata_mode: str = "AHCI"
    sata_port1_hot_plug: str = "Disabled"
    sata_port2_hot_plug: str = "Disabled"

@dataclass
class AdvancedOnboardDevicesConfig:
    onboard_led_in_s5: str = "Disabled"
    restore_onboard_led_default: str = "Disabled"
    rgb_led: str = "On"
    display_priority: str = "External Graphic"
    onboard_hd_audio: str = "Enabled"
    onboard_lan: str = "Enabled"
    wan_radio: str = "Enabled"
    bt_on_off: str = "Enabled"
    onboard_debug_port_led: str = "Runtime CPU tempe."
    onboard_button_led: str = "On"

@dataclass
class AdvancedTrustedComputingConfig:
    firmware_version: str = "6.32"
    vendor: str = "AMD"
    security_device_support: str = "Enable"
    active_pcr_banks: str = "SHA256"
    available_pcr_banks: str = "SHA256, SHA384"
    sha256_pcr_bank: str = "Enabled"
    sha384_pcr_bank: str = "Disabled"
    pending_operation: str = "None"
    platform_hierarchy: str = "Enabled"
    storage_hierarchy: str = "Enabled"
    endorsement_hierarchy: str = "Enabled"
    physical_presence_spec_version: str = "1.3"
    device_select_tc: str = "Auto"
    disable_block_sid: str = "Disabled"

@dataclass
class AmdOverclockingConfig:
    pbo_mode: str = "Advanced"
    pbo_limits_mode: str = "Auto"
    pbo_ppt_limit: int = 0
    pbo_tdc_limit: int = 0
    pbo_edc_limit: int = 0
    pbo_scalar_ctrl_mode: str = "Auto"
    pbo_scalar_value: str = "Auto"
    cpu_boost_clock_override: str = "Enabled (Positive)"
    max_cpu_boost_clock_override: int = 200
    platform_thermal_throttle_ctrl_adv_mode: str = "Auto"
    platform_thermal_throttle_limit_adv_value: int = 95
    curve_optimizer_mode: str = "Disabled"
    all_core_sign: str = "Negative"
    all_core_magnitude: int = 0
    per_core_optimizers: List[PerCoreCurveOptimizer] = field(default_factory=lambda: _create_list(PerCoreCurveOptimizer, 8))
    curve_shapers: List[CurveShaperSetting] = field(default_factory=lambda: _create_list(CurveShaperSetting, 15))
    ddr_pmu_training: str = "Auto"
    ddr_turnaround_times: str = "Auto"
    ddr5_nitro_mode: str = "Enable"
    ddr5_robust_training_mode: str = "Enable"
    nitro_rx_data: int = 2
    nitro_tx_data: int = 3
    nitro_control_line: int = 1
    nitro_rx_burst_length: str = "Auto"
    nitro_tx_burst_length: str = "Auto"
    nitro_dfe_vref_offset_limits: str = "Auto"
    nitro_tx_dfe_gain_bias_po: str = "Auto"
    nitro_rx_dfe_gain_bias: str = "Auto"

@dataclass
class AmdCbsConfig:
    # CPU Common
    redirect_for_return_dis: str = "Auto"
    core_performance_boost: str = "Auto"
    global_cstate_control: str = "Disabled"
    power_supply_idle_control: str = "Typical Current Idle"
    opcache_control: str = "Enabled"
    streaming_stores_control: str = "Auto"
    local_apic_mode: str = "Auto"
    acpi_cst_c1_declaration: str = "Auto"
    platform_first_error_handling: str = "Auto"
    mca_error_thresh_enable: str = "Auto"
    mca_fru_text: str = "True"
    smu_psp_debug_mode: str = "Auto"
    ppin_opt_in: str = "Auto"
    rep_mov_stos_streaming: str = "Auto"
    enhanced_rep_movsb_stosb: str = "Auto"
    fast_short_rep_movsb_fsrm: str = "Auto"
    snp_memory_rmp_table_coverage: str = "Auto"
    smee: str = "Auto"
    action_on_bist_failure: str = "Auto"
    log_transparent_errors: str = "Auto"
    avx512_cbs: str = "Enabled"
    monitor_mwait_disable: str = "Auto"
    corrector_branch_predictor: str = "Enabled"
    pause_delay: str = "Auto"
    cpu_speculative_store_modes: str = "More Speculative"
    svm_lock: str = "Auto"
    svm_enable: str = "Auto"
    lul: str = "Enabled"
    # Prefetcher
    l1_stream_hw_prefetcher: str = "Enable"
    l2_stream_hw_prefetcher: str = "Enable"
    l1_stride_prefetcher: str = "Enable"
    l1_region_prefetcher: str = "Enable"
    l1_burst_prefetch_mode: str = "Enable"
    l2_up_down_prefetcher: str = "Enable"
    # SMU Common
    cppc_dynamic_preferred_cores: str = "Cache"
    smu_tdp_control_mode: str = "Auto"
    smu_tdp_control_value: int = 0
    eco_mode: str = "Disable"
    smu_ppt_control_mode: str = "Auto"
    smu_ppt_control_value: int = 0
    smu_thermal_control_mode: str = "Auto"
    smu_thermal_control_value: int = 0
    smu_tdc_control_mode: str = "Auto"
    smu_tdc_control_value: int = 0
    smu_edc_control_mode: str = "Auto"
    smu_edc_control_value: int = 0
    smu_vddp_voltage_control_mode: str = "Auto"
    smu_vddp_voltage_control_value: int = 0
    smu_infinity_fabric_frequency: str = "2000"
    sync_fifo_mode_override: str = "Auto"
    sustained_power_limit: int = 0
    fast_ppt_limit: int = 0
    slow_ppt_limit: int = 0
    slow_ppt_time_constant: int = 0
    gfxoff: str = "Disable"
    # DF Common
    memory_interleaving: str = "Enabled"
    memory_interleaving_size: str = "Auto"
    dram_map_inversion: str = "Auto"
    location_of_private_memory_regions: str = "Consolidated to 1st die"
    # SOC Misc
    soc_tpm: str = "Auto"
    pluton_security_processor: str = "Disabled"
    drtm_support: str = "Auto"
    smm_isolation_support: str = "Auto"
    abl_console_out_control: str = "Auto"
    app_compatibility_database: str = "Enabled"

@dataclass
class AmdPbsConfig:
    unused_gpp_clocks_off: str = "Disabled"
    pm_l1_ss: str = "Disabled"
    pcie_gfx_lanes_config: str = "Auto"
    pcie_x16_link_speed: str = "Auto"
    pcie_x4_link_speed: str = "Auto"
    m2_1_config: str = "Enabled"
    m2_1_link_speed: str = "Auto"
    chipset_link_speed: str = "Auto"
    bclk_control_mode: str = "Auto"
    bclk_value: float = 100.00
    nvme_raid_mode: str = "Disabled"
    thunderbolt_support: str = "Enabled"

@dataclass
class AdvancedSettings:
    cpu_config: AdvancedCpuConfig = field(default_factory=AdvancedCpuConfig)
    acpi_config: AdvancedAcpiConfig = field(default_factory=AdvancedAcpiConfig)
    storage_config: AdvancedStorageConfig = field(default_factory=AdvancedStorageConfig)
    onboard_devices_config: AdvancedOnboardDevicesConfig = field(default_factory=AdvancedOnboardDevicesConfig)
    trusted_computing_config: AdvancedTrustedComputingConfig = field(default_factory=AdvancedTrustedComputingConfig)
    amd_overclocking: AmdOverclockingConfig = field(default_factory=AmdOverclockingConfig)
    amd_cbs: AmdCbsConfig = field(default_factory=AmdCbsConfig)
    amd_pbs: AmdPbsConfig = field(default_factory=AmdPbsConfig)
    notes: str = ""

@dataclass
class FanControlSettings:
    mode: str = "Customize"
    step_up_seconds: str = "Auto"
    step_down_seconds: str = "Auto"
    speed_points: List[FanSpeedPoint] = field(default_factory=lambda: [FanSpeedPoint(40,20), FanSpeedPoint(60,50), FanSpeedPoint(75,90), FanSpeedPoint(80,100)])
    critical_temp: int = 85
    allow_fan_stop: Optional[str] = None # Only for MOS fan
    fan_on_off: Optional[str] = None # Only for MOS fan

@dataclass
class HwMonitorSettings:
    cpu_fan1: FanControlSettings = field(default_factory=FanControlSettings)
    mos_fan1: FanControlSettings = field(default_factory=lambda: FanControlSettings(allow_fan_stop="Disabled", fan_on_off="Auto", speed_points=[FanSpeedPoint(40,30), FanSpeedPoint(60,60), FanSpeedPoint(75,90), FanSpeedPoint(85,100)]))
    cpu_fan2_wp_switch_mode: str = "W_PUMP"
    aio_pump_control_mode: str = "Auto"
    aio_pump_setting: str = "Performance Mode"
    aio_pump_temp_source: str = "Monitor CPU"
    w_pump_control_mode: str = "Auto"
    w_pump_setting: str = "Performance Mode"
    w_pump_temp_source: str = "Monitor CPU"
    notes: str = ""

@dataclass
class ToolSettings:
    easy_raid_installer: str = ""
    ssd_secure_erase: str = ""
    nvme_sanitization: str = ""
    instant_flash: str = ""
    auto_driver_installer: str = "Enabled"
    notes: str = ""

@dataclass
class BootSettings:
    boot_option1: str = ""
    boot_option2: str = ""
    boot_option3: str = ""
    csm_support: str = "Disabled"
    pxe_oprom_policy: str = "Do not launch"
    storage_oprom_policy: str = "Do not launch"
    setup_prompt_timeout: int = 1
    bootup_num_lock: str = "On"
    full_screen_logo: str = "Enabled"
    fast_boot: str = "Disabled"
    notes: str = ""

@dataclass
class SecuritySettings:
    system_mode_state: str = "User"
    secure_boot_enable: str = "Enabled"
    secure_boot_mode: str = "Standard"
    notes: str = ""

@dataclass
class ExitSettings:
    notes: str = ""

T = TypeVar('T')

def _from_dict(cls: Type[T], data: dict) -> T:
    if not isinstance(data, dict):
        return data
    
    kwargs = {}
    for f in fields(cls):
        if f.name in data:
            field_value = data[f.name]
            field_type = f.type

            if is_dataclass(field_type) and isinstance(field_value, dict):
                kwargs[f.name] = _from_dict(field_type, field_value)
            elif (hasattr(field_type, '__origin__') and field_type.__origin__ is list and
                  len(field_type.__args__) > 0 and is_dataclass(field_type.__args__[0]) and 
                  isinstance(field_value, list)):
                item_cls = field_type.__args__[0]
                kwargs[f.name] = [_from_dict(item_cls, item) for item in field_value]
            else:
                kwargs[f.name] = field_value
    return cls(**kwargs)

@dataclass
class Profile:

    def to_html_tool_dict(self) -> dict:
        """
        Returns a dictionary representation of the profile suitable for export to the HTML tool.
        This flattens the main fields and includes all relevant settings for round-trip compatibility.
        """
        # Top-level fields
        d = {
            'profileName': self.name,
            'profileNotes': self.description,
            'biosVersion': getattr(self.main, 'bios_version', ''),
            'mainNotes': getattr(self.main, 'notes', ''),
        }
        # OC Tweaker
        oc = self.oc_tweaker
        d.update({
            'dramFrequency': getattr(oc, 'dram_frequency', ''),
            'memoryContextRestore': getattr(oc, 'memory_context_restore', ''),
            'vddioVoltage': getattr(oc, 'vddio_voltage', ''),
            'dramVddVoltage': getattr(oc, 'dram_vdd_voltage', ''),
            'dramVddqVoltage': getattr(oc, 'dram_vddq_voltage', ''),
            'dramProfileSetting': getattr(oc, 'dram_profile_setting', ''),
            'dramPerformanceMode': getattr(oc, 'dram_performance_mode', ''),
            'ocTweakerNotes': getattr(oc, 'notes', ''),
        })
        # DRAM Timings (if present)
        timings = getattr(oc, 'dram_timings', None)
        if timings:
            d.update({
                'dramTcl': getattr(timings, 'tcl', ''),
                'dramTrcdrd': getattr(timings, 'trcdrd', ''),
                'dramTrp': getattr(timings, 'trp', ''),
                'dramTras': getattr(timings, 'tras', ''),
                'dramTrc': getattr(timings, 'trc', ''),
            })
        # Advanced
        d['advancedNotes'] = getattr(self.advanced, 'notes', '')
        # H/W Monitor
        d['hwMonitorNotes'] = getattr(self.hw_monitor, 'notes', '')
        # Tool
        tool = self.tool
        d.update({
            'easyRaidInstaller': getattr(tool, 'easy_raid_installer', ''),
            'ssdSecureErase': getattr(tool, 'ssd_secure_erase', ''),
            'nvmeSanitization': getattr(tool, 'nvme_sanitization', ''),
            'instantFlash': getattr(tool, 'instant_flash', ''),
            'autoDriverInstaller': getattr(tool, 'auto_driver_installer', ''),
            'toolNotes': getattr(tool, 'notes', ''),
        })
        # Boot
        boot = self.boot
        d.update({
            'bootOption1': getattr(boot, 'boot_option1', ''),
            'bootOption2': getattr(boot, 'boot_option2', ''),
            'bootOption3': getattr(boot, 'boot_option3', ''),
            'csmSupport': getattr(boot, 'csm_support', ''),
            'pxeOpromPolicy': getattr(boot, 'pxe_oprom_policy', ''),
            'storageOpromPolicy': getattr(boot, 'storage_oprom_policy', ''),
            'setupPromptTimeout': getattr(boot, 'setup_prompt_timeout', ''),
            'bootupNumlock': getattr(boot, 'bootup_num_lock', ''),
            'fullScreenLogo': getattr(boot, 'full_screen_logo', ''),
            'fastBoot': getattr(boot, 'fast_boot', ''),
            'bootNotes': getattr(boot, 'notes', ''),
        })
        # Security
        sec = self.security
        d.update({
            'systemModeState': getattr(sec, 'system_mode_state', ''),
            'secureBootEnable': getattr(sec, 'secure_boot_enable', ''),
            'secureBootMode': getattr(sec, 'secure_boot_mode', ''),
            'securityNotes': getattr(sec, 'notes', ''),
        })
        # Exit
        d['exitNotes'] = getattr(self.exit, 'notes', '')
        return d

    def to_formatted_string(self) -> str:
        """
        Returns a human-readable string representation of the profile for display in the UI.
        """
        lines = [f"Profile: {self.name}", f"Description: {self.description}"]
        lines.append(f"BIOS Version: {getattr(self.main, 'bios_version', '')}")
        lines.append(f"Processor: {getattr(self.main, 'processor_type', '')}")
        lines.append(f"Max Speed: {getattr(self.main, 'max_speed', '')}")
        lines.append(f"Total Memory: {getattr(self.main, 'total_memory', '')}")
        lines.append(f"Main Notes: {getattr(self.main, 'notes', '')}")
        lines.append("\n[OC Tweaker]")
        oc = self.oc_tweaker
        lines.append(f"DRAM Frequency: {getattr(oc, 'dram_frequency', '')}")
        lines.append(f"Memory Context Restore: {getattr(oc, 'memory_context_restore', '')}")
        lines.append(f"VDDIO Voltage: {getattr(oc, 'vddio_voltage', '')}")
        lines.append(f"DRAM VDD Voltage: {getattr(oc, 'dram_vdd_voltage', '')}")
        lines.append(f"DRAM VDDQ Voltage: {getattr(oc, 'dram_vddq_voltage', '')}")
        lines.append(f"DRAM Profile Setting: {getattr(oc, 'dram_profile_setting', '')}")
        lines.append(f"DRAM Performance Mode: {getattr(oc, 'dram_performance_mode', '')}")
        lines.append(f"OC Tweaker Notes: {getattr(oc, 'notes', '')}")
        # DRAM Timings
        timings = getattr(oc, 'dram_timings', None)
        if timings:
            lines.append("\n[DRAM Timings]")
            lines.append(f"tCL: {getattr(timings, 'tcl', '')}")
            lines.append(f"tRCDRD: {getattr(timings, 'trcdrd', '')}")
            lines.append(f"tRP: {getattr(timings, 'trp', '')}")
            lines.append(f"tRAS: {getattr(timings, 'tras', '')}")
            lines.append(f"tRC: {getattr(timings, 'trc', '')}")
        lines.append("\n[Advanced]")
        lines.append(f"Notes: {getattr(self.advanced, 'notes', '')}")
        lines.append("\n[H/W Monitor]")
        lines.append(f"Notes: {getattr(self.hw_monitor, 'notes', '')}")
        lines.append("\n[Tool]")
        tool = self.tool
        lines.append(f"Easy RAID Installer: {getattr(tool, 'easy_raid_installer', '')}")
        lines.append(f"SSD Secure Erase: {getattr(tool, 'ssd_secure_erase', '')}")
        lines.append(f"NVMe Sanitization: {getattr(tool, 'nvme_sanitization', '')}")
        lines.append(f"Instant Flash: {getattr(tool, 'instant_flash', '')}")
        lines.append(f"Auto Driver Installer: {getattr(tool, 'auto_driver_installer', '')}")
        lines.append(f"Tool Notes: {getattr(tool, 'notes', '')}")
        lines.append("\n[Boot]")
        boot = self.boot
        lines.append(f"Boot Option 1: {getattr(boot, 'boot_option1', '')}")
        lines.append(f"Boot Option 2: {getattr(boot, 'boot_option2', '')}")
        lines.append(f"Boot Option 3: {getattr(boot, 'boot_option3', '')}")
        lines.append(f"CSM Support: {getattr(boot, 'csm_support', '')}")
        lines.append(f"PXE OpROM Policy: {getattr(boot, 'pxe_oprom_policy', '')}")
        lines.append(f"Storage OpROM Policy: {getattr(boot, 'storage_oprom_policy', '')}")
        lines.append(f"Setup Prompt Timeout: {getattr(boot, 'setup_prompt_timeout', '')}")
        lines.append(f"Bootup Numlock: {getattr(boot, 'bootup_num_lock', '')}")
        lines.append(f"Full Screen Logo: {getattr(boot, 'full_screen_logo', '')}")
        lines.append(f"Fast Boot: {getattr(boot, 'fast_boot', '')}")
        lines.append(f"Boot Notes: {getattr(boot, 'notes', '')}")
        lines.append("\n[Security]")
        sec = self.security
        lines.append(f"System Mode State: {getattr(sec, 'system_mode_state', '')}")
        lines.append(f"Secure Boot Enable: {getattr(sec, 'secure_boot_enable', '')}")
        lines.append(f"Secure Boot Mode: {getattr(sec, 'secure_boot_mode', '')}")
        lines.append(f"Security Notes: {getattr(sec, 'notes', '')}")
        lines.append("\n[Exit]")
        lines.append(f"Exit Notes: {getattr(self.exit, 'notes', '')}")
        return '\n'.join(lines)
    id: Optional[int] = None
    name: str = "New Profile"
    description: str = ""
    main: MainSettings = field(default_factory=MainSettings)
    oc_tweaker: OcTweakerSettings = field(default_factory=OcTweakerSettings)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)
    hw_monitor: HwMonitorSettings = field(default_factory=HwMonitorSettings)
    tool: ToolSettings = field(default_factory=ToolSettings)
    boot: BootSettings = field(default_factory=BootSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    exit: ExitSettings = field(default_factory=ExitSettings)

    def to_json(self) -> str:
        """Serializes the entire profile into a JSON string."""
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @staticmethod
    def from_json(json_str: str) -> "Profile":
        """Deserializes a JSON string into a Profile object."""
        data = json.loads(json_str)
        return _from_dict(Profile, data)

    def to_settings_list(self) -> List[dict]:
        """
        Serializes the profile to a list of dictionaries for database storage.
        We store the entire profile as a single JSON string.
        """
        return [{'key': 'profile_json', 'value': self.to_json(), 'type': 'json'}]

    @staticmethod
    def from_settings_list(settings: List[dict]) -> "Profile":
        """
        Deserializes a list of settings (containing one JSON string) 
        into a Profile object.
        """
        for setting in settings:
            if setting.get('key') == 'profile_json' and setting.get('type') == 'json':
                return Profile.from_json(setting['value'])
        return Profile()

def safe_int(val, default=0):
    try:
        if val is None or val == '':
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def load_from_json_file(file_path: str) -> Optional['Profile']:
    """
    Loads a profile from a JSON file exported by the HTML tool, mapping fields to the correct nested dataclass structure.
    Robust to missing/blank fields.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        profile = Profile()

        # Top-level metadata
        profile.name = data.get('profileName', 'Imported Profile')
        profile.description = data.get('profileNotes', '')

        # Main BIOS info (if present)
        profile.main.bios_version = data.get('biosVersion', '')
        profile.main.notes = data.get('mainNotes', '')

        # OC Tweaker
        tweaker = profile.oc_tweaker
        tweaker.dram_frequency = data.get('dramFrequency', tweaker.dram_frequency)
        tweaker.memory_context_restore = data.get('memoryContextRestore', tweaker.memory_context_restore)
        tweaker.vddio_voltage = data.get('vddioVoltage', tweaker.vddio_voltage)
        tweaker.dram_vdd_voltage = data.get('dramVddVoltage', tweaker.dram_vdd_voltage)
        tweaker.dram_vddq_voltage = data.get('dramVddqVoltage', tweaker.dram_vddq_voltage)
        tweaker.dram_profile_setting = data.get('dramProfileSetting', tweaker.dram_profile_setting)
        tweaker.dram_performance_mode = data.get('dramPerformanceMode', tweaker.dram_performance_mode)
        tweaker.notes = data.get('ocTweakerNotes', tweaker.notes)

        # DRAM Timings
        timings = tweaker.dram_timings
        timings.tcl = safe_int(data.get('dramTcl', timings.tcl))
        timings.trcdrd = safe_int(data.get('dramTrcdrd', timings.trcdrd))
        timings.trp = safe_int(data.get('dramTrp', timings.trp))
        timings.tras = safe_int(data.get('dramTras', timings.tras))
        timings.trc = safe_int(data.get('dramTrc', timings.trc))

        # Advanced
        adv = profile.advanced
        adv.notes = data.get('advancedNotes', adv.notes)

        # H/W Monitor
        hw = profile.hw_monitor
        hw.notes = data.get('hwMonitorNotes', hw.notes)

        # Tool
        tool = profile.tool
        tool.easy_raid_installer = data.get('easyRaidInstaller', tool.easy_raid_installer)
        tool.ssd_secure_erase = data.get('ssdSecureErase', tool.ssd_secure_erase)
        tool.nvme_sanitization = data.get('nvmeSanitization', tool.nvme_sanitization)
        tool.instant_flash = data.get('instantFlash', tool.instant_flash)
        tool.auto_driver_installer = data.get('autoDriverInstaller', tool.auto_driver_installer)
        tool.notes = data.get('toolNotes', tool.notes)

        # Boot
        boot = profile.boot
        boot.boot_option1 = data.get('bootOption1', boot.boot_option1)
        boot.boot_option2 = data.get('bootOption2', boot.boot_option2)
        boot.boot_option3 = data.get('bootOption3', boot.boot_option3)
        boot.csm_support = data.get('csmSupport', boot.csm_support)
        boot.pxe_oprom_policy = data.get('pxeOpromPolicy', boot.pxe_oprom_policy)
        boot.storage_oprom_policy = data.get('storageOpromPolicy', boot.storage_oprom_policy)
        boot.setup_prompt_timeout = safe_int(data.get('setupPromptTimeout', boot.setup_prompt_timeout))
        boot.bootup_num_lock = data.get('bootupNumlock', boot.bootup_num_lock)
        boot.full_screen_logo = data.get('fullScreenLogo', boot.full_screen_logo)
        boot.fast_boot = data.get('fastBoot', boot.fast_boot)
        boot.notes = data.get('bootNotes', boot.notes)

        # Security
        sec = profile.security
        sec.system_mode_state = data.get('systemModeState', sec.system_mode_state)
        sec.secure_boot_enable = data.get('secureBootEnable', sec.secure_boot_enable)
        sec.secure_boot_mode = data.get('secureBootMode', sec.secure_boot_mode)
        sec.notes = data.get('securityNotes', sec.notes)

        # Exit
        profile.exit.notes = data.get('exitNotes', profile.exit.notes)

        return profile

    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"Error loading profile from {file_path}: {e}") # Replace with logging
        return None
