import json
import uuid
from typing import Dict, Any, Optional, List

class Profile:
    """
    Represents a complete BIOS profile, corresponding to one saved JSON file.

    This class holds all the settings from the various sections of the BIOS,
    making them accessible as nested dictionaries. It's designed to directly
    map to the structure of the JSON output from the HTML profiler.
    """
    def __init__(self, name: str, profile_id: Optional[str] = None, notes: Optional[str] = None):
        """
        Initializes a Profile object.

        Args:
            name (str): The name of the profile (e.g., "Nova Gaming OC v1.5").
            profile_id (Optional[str]): A unique identifier for the profile. 
                                        If not provided, a new UUID will be generated.
            notes (Optional[str]): General notes for the entire profile.
        """
        self.id: str = profile_id if profile_id else str(uuid.uuid4())
        self.name: str = name
        self.notes: Optional[str] = notes
        # Each key in this dictionary represents a major section from the HTML form.
        # The value is another dictionary containing all settings for that section.
        self.settings: Dict[str, Dict[str, Any]] = {
            "main": {},
            "oc_tweaker": {},
            "dram_timing": {},
            "advanced": {},
            "advanced_amd_overclocking": {},
            "advanced_amd_cbs": {},
            "advanced_amd_pbs": {},
            "hw_monitor": {},
            "boot": {},
            "security": {}
        }

    def __repr__(self) -> str:
        """Provides a developer-friendly representation of the Profile."""
        return f"Profile(id='{self.id}', name='{self.name}', settings_sections={list(self.settings.keys())})"

    def get_setting(self, section: str, setting_name: str) -> Any:
        """
        Retrieves a specific setting from a given section.

        Args:
            section (str): The section key (e.g., 'oc_tweaker').
            setting_name (str): The specific setting's ID (e.g., 'dramFrequency').

        Returns:
            The value of the setting, or None if not found.
        """
        return self.settings.get(section, {}).get(setting_name)

def _get_section_keys() -> Dict[str, List[str]]:
    """
    Internal helper to define which HTML input IDs belong to which section.
    This mapping is crucial for correctly structuring the loaded data.
    The keys here match the keys in the Profile.settings dictionary.
    """
    return {
        "main": ["biosVersion", "processorType", "maxSpeed", "totalMemory", "dramA1", "dramA2", "dramB1", "dramB2", "mainNotes"],
        "oc_tweaker": [
            "gamingMode", "zen5GamingOptimizations", "tdpTo105W", "performanceBoost", "performancePreset", 
            "platformThermalThrottleLimitTjMax", "cpuOverclocking", "gfxOverclocking", "dramProfileSetting", 
            "dramPerformanceMode", "dramFrequency", "memoryContextRestore", "vddioVoltage", "dramVddVoltage", 
            "dramVddqVoltage", "dramVppVoltage", "ocInfinityFabricFrequency", "uclkDivMode", "ocVddSocDirect", 
            "ocVddMiscDirect", "ocVddgCcdVoltage", "ocVddgIodVoltage", "ocVddpVoltage", "ocBusSpeedMode", 
            "vddcrCpuVoltage", "vddcrCpuLlc", "vddcrSocVoltage", "vddcrSocLlc", "vddMiscVoltageExt", 
            "vddMiscS5Voltage", "pch1_105Voltage", "pch2_105Voltage", "pch18Voltage", "ocTweakerNotes"
        ],
        "dram_timing": [
            "tCL", "tRCDRD", "tRP", "tRAS", "tRC", "tWR", "tREFI", "tRFC1", "tRFC2", "tRFCSb", "tRTP", 
            "tRRD_L", "tRRD_S", "tFAW", "tWTR_L", "tWTR_S", "TrdrdScL", "TrdrdSc", "TrdrdSd", "TrdrdDd", 
            "TwrwrScL", "TwrwrSc", "TwrwrSd", "TwrwrDd", "Twrrd", "Trdwr", "dramOdtRttNomRd", "dramOdtRttNomWr", 
            "dramOdtRttWr", "dramOdtRttPark", "dramOdtDqsRttPark", "dramDqDriveStr", "procOdtImpedance", 
            "procDqDriveStr", "procCaDriveStr", "dramTimingNotes"
        ],
        "advanced": [
            "cpuFamily", "cpuModel", "cpuId", "microcodePatch", "l1InstCache", "l1DataCache", "l2Cache", 
            "totalL3Cache", "amdFtpmSwitch", "pssSupport", "nxMode", "smtMode", "advAvx512", "suspendToRam", 
            "restoreOnAcPowerLoss", "deepSleep", "usbDevicePowerOn", "usbPowerDeliveryS5", "pcieDevicesPowerOn", 
            "rtcAlarmPowerOn", "sataMode", "sataPort1HotPlug", "sataPort2HotPlug", "sataM2Detected", 
            "sataPort1Detected", "sataPort2Detected", "sataPortA1Detected", "sataPortA2Detected", "nvmeDevice1Info", 
            "nvmeDevice2Info", "onboardLedInS5", "restoreOnboardLedDefault", "rgbLed", "displayPriority", 
            "onboardHdAudio", "onboardLan", "wanRadio", "btOnOff", "onboardDebugPortLed", "onboardButtonLed", 
            "tcFirmwareVersion", "tcVendor", "securityDeviceSupport", "activePcrBanks", "availablePcrBanks", 
            "sha256PcrBank", "sha384PcrBank", "pendingOperation", "platformHierarchy", "storageHierarchy", 
            "endorsementHierarchy", "physicalPresenceSpecVersion", "deviceSelectTc", "disableBlockSid", "advancedNotes"
        ],
        "advanced_amd_overclocking": [
            "pboMode", "pboLimits", "pboScalarCtrl", "pboScalar", "cpuBoostClockOverride", "maxCpuBoostClockOverride", 
            "platformThermalThrottleCtrlAdv", "platformThermalThrottleLimitAdv", "curveOptimizerMode", 
            # Per-core and Curve Shaper settings are dynamically generated in the HTML, so we handle them specially.
            "ddrPmuTraining", "ddrTurnaroundTimes", "ddr5NitroMode", "ddr5RobustTrainingMode", "nitroRxData", 
            "nitroTxData", "nitroControlLine", "nitroRxBurstLength", "nitroTxBurstLength", "nitroDfeVrefOffsetLimits", 
            "nitroTxDfeGainBiasPo", "nitroRxDfeGainBias", "advAmdOcNotes"
        ],
        "advanced_amd_cbs": [
            "redirectForReturnDis", "corePerformanceBoost", "globalCstateControl", "powerSupplyIdleControl", "opcacheControl", 
            "streamingStoresControl", "localApicMode", "acpiCstC1Declaration", "platformFirstErrorHandling", 
            "mcaErrorThreshEnable", "mcaFruText", "smuPspDebugMode", "ppinOptIn", "repMovStosStreaming", 
            "enhancedRepMovsbStosb", "fastShortRepMovsbFsrm", "snpMemoryRmpTableCoverage", "smee", "actionOnBistFailure", 
            "logTransparentErrors", "avx512", "monitorMwaitDisable", "correctorBranchPredictor", "pauseDelay", 
            "cpuSpeculativeStoreModes", "svmLock", "svmEnable", "lul", "l1StreamHWPrefetcher", "l2StreamHWPrefetcher", 
            "l1StridePrefetcher", "l1RegionPrefetcher", "l1BurstPrefetchMode", "l2UpDownPrefetcher", "cppcDynamicPreferredCores", 
            "tdpControl", "ecoMode", "pptControl", "thermalControl", "tdcControl", "edcControl", "vddpVoltageControl", 
            "smuInfinityFabricFrequency", "syncFifoModeOverride", "sustainedPowerLimit", "fastPPTLimit", "slowPPTLimit", 
            "slowPPTTimeConstant", "gfxoff", "memoryInterleaving", "memoryInterleavingSize", "dramMapInversion", 
            "locationOfPrivateMemoryRegions", "socTpm", "plutonSecurityProcessor", "drtmSupport", "smmIsolationSupport", 
            "ablConsoleOutControl", "appCompatibilityDatabase", "advAmdCbsNotes"
        ],
        "advanced_amd_pbs": [
            "unusedGppClocksOff", "pmL1Ss", "pcieGfxLanesConfig", "pcieX16LinkSpeed", "pcieX4LinkSpeed", 
            "m2_1Config", "m2_1LinkSpeed", "chipsetLinkSpeed", "bclkControlMode", "nvmeRaidMode", 
            "thunderboltSupport", "advAmdPbsNotes"
        ],
        "hw_monitor": [
            "cpuFan1Mode", "cpuFan1StepUp", "cpuFan1StepDown", "cpuFan1Temp1", "cpuFan1Duty1", "cpuFan1Temp2", 
            "cpuFan1Duty2", "cpuFan1Temp3", "cpuFan1Duty3", "cpuFan1Temp4", "cpuFan1Duty4", "cpuFan1CriticalTemp", 
            "mosFan1Mode", "mosFan1Temp1", "mosFan1Duty1", "mosFan1Temp2", "mosFan1Duty2", "mosFan1Temp3", 
            "mosFan1Duty3", "mosFan1Temp4", "mosFan1Duty4", "mosFan1CriticalTemp", "mosFanAllowStop", "mosFanOnOff",
            "cpuFan2WpSwitch", "aioPumpControlMode", "aioPumpSetting", "wPumpControlMode", "wPumpSetting", 
            "wPumpTempSource", "hwMonitorNotes"
        ],
        "boot": [
            "bootOption1", "bootOption2", "bootOption3", "csmSupport", "pxeOpromPolicy", "storageOpromPolicy", 
            "setupPromptTimeout", "bootupNumLock", "fullScreenLogo", "fastBoot", "bootNotes"
        ],
        "security": ["systemModeState", "secureBootEnable", "secureBootMode", "securityNotes"]
    }

def load_profile_from_json(filepath: str) -> Optional[Profile]:
    """
    Loads a BIOS profile from a JSON file generated by the HTML tool.

    This function reads the flat key-value structure of the JSON and organizes
    it into the hierarchical Profile object structure.

    Args:
        filepath (str): The path to the .json profile file.

    Returns:
        A populated Profile object, or None if an error occurs.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing JSON file: {e}")
        return None

    profile_name = data.pop('profileName', 'Unnamed Profile')
    profile = Profile(name=profile_name)

    section_keys = _get_section_keys()

    # Handle dynamically generated fields (Curve Optimizer, Curve Shaper)
    co_settings = {}
    cs_settings = {}
    other_data = {}

    for key, value in data.items():
        if key.startswith('core') and ('Sign' in key or 'Magnitude' in key):
            co_settings[key] = value
        elif key.startswith('cs'):
            cs_settings[key] = value
        else:
            other_data[key] = value
            
    if co_settings:
        profile.settings['advanced_amd_overclocking']['curve_optimizer_per_core'] = co_settings
    if cs_settings:
        profile.settings['advanced_amd_overclocking']['curve_shaper'] = cs_settings

    # Distribute the remaining settings into their respective sections
    for section_name, keys in section_keys.items():
        for key in keys:
            if key in other_data:
                profile.settings[section_name][key] = other_data.pop(key)

    # Any leftover data not in our mapping can be put in a misc section
    if other_data:
        profile.settings['miscellaneous'] = other_data
        
    return profile

def save_profile_to_json(profile: Profile, filepath: str) -> None:
    """
    Saves a Profile object to a JSON file.

    This function flattens the Profile object's structure back into a format
    that resembles the original JSON, which could potentially be loaded back
    into the HTML tool.

    Args:
        profile (Profile): The Profile object to save.
        filepath (str): The path where the .json file will be saved.
    """
    output_data = {'profileName': profile.name}
    for section_data in profile.settings.values():
        for key, value in section_data.items():
            # Handle nested dictionaries like curve optimizer
            if isinstance(value, dict):
                output_data.update(value)
            else:
                output_data[key] = value
    
    try:
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Profile '{profile.name}' saved successfully to {filepath}")
    except IOError as e:
        print(f"Error saving file: {e}")


# --- Example Usage ---
if __name__ == '__main__':
    # This block demonstrates how to use the functions in this module.
    # To run this, you must first save a profile from your HTML tool.
    # 1. Open "BIOS Profile Saver.html" in your browser.
    # 2. Fill in some values.
    # 3. Enter a profile name, e.g., "MyTestProfile".
    # 4. Click "Save Profile to File". It will save "mytestprofile_v1.5.json".
    # 5. Place that JSON file in the same directory as this script.
    
    # NOTE: You will need to change the filename here to match the one you saved.
    json_filename = 'mytestprofile_v1_5.json' # <-- CHANGE THIS FILENAME

    print(f"--- Attempting to load profile: {json_filename} ---")
    my_profile = load_profile_from_json(json_filename)

    if my_profile:
        print("\nProfile loaded successfully!")
        print(f"  Profile Name: {my_profile.name}")
        print(f"  Profile ID: {my_profile.id}")

        print("\n--- Accessing specific settings ---")
        dram_freq = my_profile.get_setting('oc_tweaker', 'dramFrequency')
        tcl = my_profile.get_setting('dram_timing', 'tCL')
        pbo_mode = my_profile.get_setting('advanced_amd_overclocking', 'pboMode')
        
        print(f"  DRAM Frequency: {dram_freq}")
        print(f"  tCL: {tcl}")
        print(f"  PBO Mode: {pbo_mode}")
        
        # Accessing a whole section
        print("\n--- OC Tweaker Section Data ---")
        oc_tweaker_settings = my_profile.settings.get('oc_tweaker')
        if oc_tweaker_settings:
            for key, value in list(oc_tweaker_settings.items())[:5]: # Print first 5 for brevity
                 print(f"  {key}: {value}")
        
        # Accessing dynamically generated Curve Optimizer data
        print("\n--- Curve Optimizer Data ---")
        co_data = my_profile.get_setting('advanced_amd_overclocking', 'curve_optimizer_per_core')
        if co_data:
             # Just show the first couple of items for the example
            for key, value in list(co_data.items())[:4]:
                print(f"  {key}: {value}")

        # --- Example of modifying and saving ---
        # print("\n--- Modifying and saving a new profile ---")
        # my_profile.name = "My Modified Test Profile"
        # my_profile.settings['oc_tweaker']['dramFrequency'] = 'DDR5-6200'
        # save_profile_to_json(my_profile, 'modified_profile.json')
    else:
        print("\nFailed to load profile.")
        print("Please ensure the JSON file exists and the filename is correct in the script.")

