# ocl_module_src/profile_editor_ui.py
# Author: System Sage
# Date: 06/15/2025
# Description: Provides a comprehensive GUI for creating and editing detailed BIOS
#              profiles, replacing the need for manual dialog-based entry.

import customtkinter
from .bios_profile import Profile

class OclProfileEditor(customtkinter.CTkToplevel):
    """A Toplevel window for creating and editing a detailed BIOS Profile."""
    def __init__(self, master, mode: str, profile_obj: Profile, callback=None):
        super().__init__(master)
        self.master = master
        self.mode = mode  # 'create' or 'edit'
        self.profile = profile_obj
        self.callback = callback
        self.widgets = {}

        self.title(f"{'Edit' if mode == 'edit' else 'New'} BIOS Profile - {self.profile.name}")
        self.geometry("1200x850") # Increased size
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()

        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        # Main frame
        main_frame = customtkinter.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Top Bar for Name and Description
        top_bar = customtkinter.CTkFrame(main_frame)
        top_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        top_bar.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(top_bar, text="Profile Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = customtkinter.CTkEntry(top_bar, width=300)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.name_entry.insert(0, self.profile.name)

        customtkinter.CTkLabel(top_bar, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = customtkinter.CTkEntry(top_bar)
        self.desc_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.desc_entry.insert(0, self.profile.description)
        
        # TabView for BIOS sections
        self.tab_view = customtkinter.CTkTabview(main_frame)
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Create tabs based on HTML structure
        self._create_tab("System Info", "_build_system_info_tab")
        self._create_tab("OC Tweaker", "_build_oc_tweaker_tab")
        self._create_tab("DRAM Timing", "_build_dram_timing_tab") # Corresponds to OC Tweaker \\ DRAM Timing Configuration
        self._create_tab("Advanced Main", "_build_advanced_main_tab") # For Advanced section (CPU, ACPI, Storage etc.)
        self._create_tab("AMD Overclocking", "_build_advanced_amd_overclocking_tab")
        self._create_tab("AMD CBS", "_build_advanced_amd_cbs_tab")
        self._create_tab("AMD PBS", "_build_advanced_amd_pbs_tab")
        self._create_tab("H/W Monitor", "_build_hw_monitor_tab")
        
        # Bottom Bar for Save/Cancel buttons
        bottom_bar = customtkinter.CTkFrame(main_frame)
        bottom_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=(10,0))
        bottom_bar.grid_columnconfigure(0, weight=1) # Center buttons
        
        button_container = customtkinter.CTkFrame(bottom_bar, fg_color="transparent")
        button_container.pack(pady=5)

        customtkinter.CTkButton(button_container, text="Save Profile", command=self._on_save).pack(side="left", padx=10)
        customtkinter.CTkButton(button_container, text="Cancel", command=self.destroy).pack(side="left", padx=10)

    def _create_tab(self, name, builder_method_name):
        tab = self.tab_view.add(name)
        # Make scroll_frame take full width of tab
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        scroll_frame = customtkinter.CTkScrollableFrame(tab, label_text=f"{name} Settings")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll_frame.grid_columnconfigure(0, weight=1) # Ensure content within scroll frame can expand
        
        builder_func = getattr(self, builder_method_name, None)
        if builder_func:
            builder_func(scroll_frame) # Pass the scroll_frame itself, not tab
        else:
            customtkinter.CTkLabel(scroll_frame, text=f"UI for {name} not implemented yet.").pack(padx=10, pady=10)

    def _add_setting_widget(self, parent, section_name, setting_id, label_text, widget_type='entry', options=None, default_value=None):
        """Helper to create a label and an input widget, and store the widget."""
        # Using a frame for each setting to manage layout better, especially for wider labels
        setting_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        setting_frame.pack(fill="x", padx=10, pady=4)
        setting_frame.grid_columnconfigure(1, weight=1) # Allow widget to expand
        
        label = customtkinter.CTkLabel(setting_frame, text=label_text, anchor="w", width=250) # Increased label width
        label.grid(row=0, column=0, sticky="w", padx=(0,5))

        widget = None
        if widget_type == 'entry':
            widget = customtkinter.CTkEntry(setting_frame)
            if default_value: widget.insert(0, str(default_value))
        elif widget_type == 'option':
            # Ensure options are strings and handle empty or None options
            str_options = [str(opt) for opt in options] if options else ["N/A"]
            widget = customtkinter.CTkOptionMenu(setting_frame, values=str_options)
            if default_value and default_value in str_options:
                widget.set(str(default_value))
            elif str_options: # Set to first option if no valid default
                widget.set(str_options[0])
        elif widget_type == 'textbox':
            widget = customtkinter.CTkTextbox(setting_frame, height=80)
            if default_value: widget.insert("1.0", str(default_value))
        
        if widget:
            widget.grid(row=0, column=1, sticky="ew")
            self.widgets[(section_name, setting_id)] = widget

    # --- UI Builder Functions for each tab ---
    def _build_system_info_tab(self, parent):
        section = "System Info" # Corresponds to HTML 'Main' section
        self._add_setting_widget(parent, section, "biosVersion", "UEFI BIOS Version:", 'entry', default_value="X870E Nova WiFi 3.20")
        self._add_setting_widget(parent, section, "processorType", "Processor Type:", 'entry', default_value="AMD Ryzen 7 9800X3D")
        self._add_setting_widget(parent, section, "maxSpeed", "Max Speed (MHz):", 'entry', default_value="5250MHz")
        self._add_setting_widget(parent, section, "totalMemory", "Total Memory (GB):", 'entry', default_value="32GB")
        customtkinter.CTkLabel(parent, text="DRAM Information (Detected)", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "dramA1", "DDR5_A1:", 'entry', default_value="Not Present")
        self._add_setting_widget(parent, section, "dramA2", "DDR5_A2:", 'entry', default_value="DDR5-4800-16GB @ 6000Mhz")
        self._add_setting_widget(parent, section, "dramB1", "DDR5_B1:", 'entry', default_value="Not Present")
        self._add_setting_widget(parent, section, "dramB2", "DDR5_B2:", 'entry', default_value="DDR5-4800-16GB @ 6000Mhz")
        self._add_setting_widget(parent, section, "mainNotes", "Main Section Notes:", 'textbox')

    def _build_oc_tweaker_tab(self, parent):
        section = "OC Tweaker"
        self._add_setting_widget(parent, section, "gamingMode", "Gaming Mode:", 'option', ["Disabled", "Enabled", "Auto"])
        self._add_setting_widget(parent, section, "zen5GamingOptimizations", "ZEN5 Gaming Optimizations:", 'option', ["Enabled", "Disabled", "Auto"])
        self._add_setting_widget(parent, section, "tdpTo105W", "TDP to 105W:", 'option', ["Disabled", "Enabled", "Auto"])
        self._add_setting_widget(parent, section, "performanceBoost", "Performance Boost:", 'entry', default_value="Cinebench_profile_2")
        self._add_setting_widget(parent, section, "performancePreset", "Performance Preset:", 'entry', default_value="PBO Enabled")
        self._add_setting_widget(parent, section, "platformThermalThrottleLimitTjMax", "Platform Thermal Throttle Limit (TjMax °C):", 'entry', default_value="90")
        
        customtkinter.CTkLabel(parent, text="DRAM Profile Configuration", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "dramProfileSetting", "DRAM Profile Setting:", 'entry', default_value="EXPO-6000 30-38-3...")
        self._add_setting_widget(parent, section, "dramPerformanceMode", "DRAM Performance Mode:", 'option', ["Aggressive", "Normal", "Auto"])
        self._add_setting_widget(parent, section, "dramFrequency", "DRAM Frequency:", 'entry', default_value="DDR5-6000")
        self._add_setting_widget(parent, section, "memoryContextRestore", "Memory Context Restore:", 'option', ["Enabled", "Disabled", "Auto"])
        
        customtkinter.CTkLabel(parent, text="Core Voltages & Frequencies", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "vddioVoltage", "VDDIO Voltage (VDDIO_MEM_S3):", 'entry', default_value="1.440V")
        self._add_setting_widget(parent, section, "dramVddVoltage", "DRAM VDD Voltage:", 'entry', default_value="1.440V")
        self._add_setting_widget(parent, section, "dramVddqVoltage", "DRAM VDDQ Voltage:", 'entry', default_value="1.440V")
        self._add_setting_widget(parent, section, "dramVppVoltage", "DRAM VPP Voltage:", 'entry', default_value="1.850V")
        self._add_setting_widget(parent, section, "ocInfinityFabricFrequency", "Infinity Fabric Frequency:", 'entry', default_value="2133 MHz")
        self._add_setting_widget(parent, section, "uclkDivMode", "UCLK DIV1 MODE:", 'option', ["UCLK=MEMCLK", "UCLK=MEMCLK/2"])
        self._add_setting_widget(parent, section, "ocVddSocDirect", "SoC/Uncore OC Voltage (VDD_SOC):", 'entry', default_value="1.200V")
        self._add_setting_widget(parent, section, "ocVddMiscDirect", "VDD Misc Voltage (Direct):", 'entry', default_value="1.200V")
        self._add_setting_widget(parent, section, "ocVddgCcdVoltage", "VDDG CCD Voltage:", 'entry', default_value="Auto")
        self._add_setting_widget(parent, section, "ocVddgIodVoltage", "VDDG IOD Voltage:", 'entry', default_value="Auto")
        self._add_setting_widget(parent, section, "ocVddpVoltage", "VDDP Voltage:", 'entry', default_value="Auto")
        
        customtkinter.CTkLabel(parent, text="External Voltage Settings", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "vddcrCpuVoltage", "VDDCR_CPU Voltage (External):", 'option', ["Auto", "Fixed Mode", "Offset Mode"])
        self._add_setting_widget(parent, section, "vddcrCpuLlc", "VDDCR_CPU Load-Line Calibration:", 'option', [f"Level {i}" for i in range(1, 6)] + ["Auto"])
        self._add_setting_widget(parent, section, "vddcrSocVoltage", "VDDCR_SOC Voltage (External):", 'option', ["Auto", "Fixed Mode", "Offset Mode"])
        self._add_setting_widget(parent, section, "vddcrSocLlc", "VDDCR_SOC Load-Line Calibration:", 'option', [f"Level {i}" for i in range(1, 6)] + ["Auto"])
        self._add_setting_widget(parent, section, "ocTweakerNotes", "OC Tweaker Notes:", 'textbox')

    def _build_dram_timing_tab(self, parent):
        section = "DRAM Timing"
        customtkinter.CTkLabel(parent, text="Primary, Secondary & Tertiary Timings", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        timings = [
            ("tCL", "CAS# Latency (tCL):", "28"), ("tRCDRD", "RAS# to CAS# Delay Read (tRCDRD):", "36"),
            ("tRP", "Row Precharge Time (tRP):", "36"), ("tRAS", "RAS# Active Time (tRAS):", "48"),
            ("tRC", "RAS# Cycle Time (tRC):", "84"), ("tWR", "Write Recovery Time (tWR):", "48"),
            ("tREFI", "Refresh Interval (tREFI):", "65528"), ("tRFC1", "Refresh Cycle Time (tRFC1):", "468"),
            ("tRFC2", "Refresh Cycle Time (tRFC2):", "254"), ("tRFCSb", "Refresh Cycle Time (tRFCSb):", "206"),
            ("tRTP", "Read to Precharge (tRTP):", "12"), ("tRRD_L", "RAS to RAS Delay (tRRD_L):", "12"),
            ("tRRD_S", "RAS to RAS Delay (tRRD_S):", "8"), ("tFAW", "Four Activate Window (tFAW):", "32"),
            ("tWTR_L", "Write to Read Delay (tWTR_L):", "24"), ("tWTR_S", "Write to Read Delay (tWTR_S):", "4")
        ]
        for id, label, default in timings:
            self._add_setting_widget(parent, section, id, label, 'entry', default_value=default)
        
        customtkinter.CTkLabel(parent, text="DRAM Bus Control Configuration", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "dramOdtRttNomRd", "Dram ODT impedance RTT_NOM_RD:", 'option', ["Auto", "RZQ/4 (60)", "RZQ/5 (48)", "RZQ/6 (40)", "RZQ/7 (34)", "Disabled"])
        self._add_setting_widget(parent, section, "dramOdtRttNomWr", "Dram ODT impedance RTT_NOM_WR:", 'option', ["Auto", "RZQ/4 (60)", "RZQ/5 (48)", "RZQ/6 (40)", "RZQ/7 (34)", "Disabled"])
        self._add_setting_widget(parent, section, "procOdtImpedance", "Processor ODT impedance (Ohms):", 'entry', default_value="60")
        self._add_setting_widget(parent, section, "dramTimingNotes", "DRAM Timing Notes:", 'textbox')

    def _build_advanced_main_tab(self, parent):
        section = "Advanced Main"
        customtkinter.CTkLabel(parent, text="CPU Configuration", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "amdFtpmSwitch", "AMD fTPM switch:", 'option', ["AMD CPU fTPM", "Disabled"])
        self._add_setting_widget(parent, section, "pssSupport", "PSS Support:", 'option', ["Enabled", "Disabled", "Auto"])
        self._add_setting_widget(parent, section, "smtMode", "SMT Mode:", 'option', ["Auto", "Enabled", "Disabled"])
        
        customtkinter.CTkLabel(parent, text="ACPI Configuration", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "suspendToRam", "Suspend to RAM:", 'option', ["Disabled", "Enabled", "Auto"])
        self._add_setting_widget(parent, section, "restoreOnAcPowerLoss", "Restore on AC/Power Loss:", 'option', ["Power Off", "Power On", "Last State"])
        
        customtkinter.CTkLabel(parent, text="Storage Configuration", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "sataMode", "SATA Mode:", 'option', ["AHCI", "RAID", "Disabled"])
        
        customtkinter.CTkLabel(parent, text="Onboard Devices Configuration", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "onboardHdAudio", "Onboard HD Audio:", 'option', ["Enabled", "Disabled", "Auto"])
        self._add_setting_widget(parent, section, "onboardLan", "Onboard LAN:", 'option', ["Enabled", "Disabled"])
        self._add_setting_widget(parent, section, "advancedNotes", "Advanced Section Notes:", 'textbox')

    def _build_advanced_amd_overclocking_tab(self, parent):
        section = "AMD Overclocking"
        customtkinter.CTkLabel(parent, text="Precision Boost Overdrive", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "pboMode", "Precision Boost Overdrive Mode:", 'option', ["Advanced", "Enabled", "Disabled", "Motherboard", "Auto"])
        self._add_setting_widget(parent, section, "pboLimits", "PBO Limits:", 'option', ["Motherboard", "Auto", "Manual", "Disabled"])
        self._add_setting_widget(parent, section, "pboScalarCtrl", "PBO Scalar Ctrl:", 'option', ["Manual", "Auto"])
        self._add_setting_widget(parent, section, "pboScalar", "PBO Scalar:", 'option', ["10X", "Auto"] + [f"{i}X" for i in range(1,10)])
        self._add_setting_widget(parent, section, "cpuBoostClockOverride", "CPU Boost Clock Override:", 'option', ["Enabled (Positive)", "Disabled", "Enabled (Negative)"])
        self._add_setting_widget(parent, section, "maxCpuBoostClockOverride", "Max CPU Boost Clock Override (+/- MHz):", 'entry', default_value="200")
        
        customtkinter.CTkLabel(parent, text="Curve Optimizer", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "curveOptimizerMode", "Curve Optimizer Mode:", 'option', ["Per Core", "All Core", "Disabled"])
        self._add_setting_widget(parent, section, "allCoreCOSign", "All Core Sign (if All Core):", 'option', ["Negative", "Positive"])
        self._add_setting_widget(parent, section, "allCoreCOMagnitude", "All Core Magnitude (if All Core):", 'entry', default_value="0")
        # Per-core settings would require more dynamic UI generation or a fixed number of core inputs
        
        customtkinter.CTkLabel(parent, text="DDR and Infinity Fabric Frequency/Timings", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "ddrPmuTraining", "DDR PMU Training:", 'option', ["Auto", "Enabled", "Disabled"])
        self._add_setting_widget(parent, section, "advAmdOcNotes", "AMD Overclocking Notes:", 'textbox')

    def _build_advanced_amd_cbs_tab(self, parent):
        section = "AMD CBS"
        customtkinter.CTkLabel(parent, text="CPU Common Options", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "corePerformanceBoost", "Core Performance Boost:", 'option', ["Auto", "Enabled", "Disabled"])
        self._add_setting_widget(parent, section, "globalCstateControl", "Global C-state Control:", 'option', ["Disabled", "Enabled", "Auto"])
        self._add_setting_widget(parent, section, "powerSupplyIdleControl", "Power Supply Idle Control:", 'option', ["Typical Current Idle", "Low Current Idle", "Auto"])
        
        customtkinter.CTkLabel(parent, text="Prefetcher settings", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "l1StreamHWPrefetcher", "L1 Stream HW Prefetcher:", 'option', ["Enable", "Disable", "Auto"])
        self._add_setting_widget(parent, section, "l2StreamHWPrefetcher", "L2 Stream HW Prefetcher:", 'option', ["Enable", "Disable", "Auto"])
        self._add_setting_widget(parent, section, "advAmdCbsNotes", "AMD CBS Notes:", 'textbox')

    def _build_advanced_amd_pbs_tab(self, parent):
        section = "AMD PBS"
        customtkinter.CTkLabel(parent, text="AMD Common Platform Module", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "pcieGfxLanesConfig", "PCIe/GFX Lanes Configuration:", 'option', ["Auto", "x8x4x4", "x16"])
        self._add_setting_widget(parent, section, "pcieX16LinkSpeed", "PCIe x16 Link Speed:", 'option', ["Auto", "Gen5", "Gen4", "Gen3", "Gen2", "Gen1"])
        self._add_setting_widget(parent, section, "nvmeRaidMode", "NVMe RAID mode:", 'option', ["Disabled", "Enabled"])
        self._add_setting_widget(parent, section, "advAmdPbsNotes", "AMD PBS Notes:", 'textbox')

    def _build_hw_monitor_tab(self, parent):
        section = "H/W Monitor"
        # These are typically read-only values in BIOS, but for logging they can be entries.
        # For a profile *setting* tool, these might not be relevant unless they are fan curve *settings*.
        # The HTML shows fan *settings*, so we include those.
        customtkinter.CTkLabel(parent, text="CPU Fan 1 Setting", font=("", 14, "bold")).pack(pady=(10,2), anchor="w", padx=10)
        self._add_setting_widget(parent, section, "cpuFan1ControlMode", "CPU Fan 1 Control Mode:", 'option', ["Auto", "DC Mode", "PWM Mode", "Voltage"])
        self._add_setting_widget(parent, section, "cpuFan1Profile", "CPU Fan 1 Profile:", 'option', ["Silent", "Standard", "Performance", "Full Speed", "Customize"])
        # Add more fan settings (temp sources, speeds) if "Customize" is chosen - complex UI
        self._add_setting_widget(parent, section, "hwMonitorNotes", "H/W Monitor Notes:", 'textbox')

    def _populate_fields(self):
        """Populate widgets with data from the profile object."""
        # Ensure settings are in the hierarchical dictionary format
        if isinstance(self.profile.settings, list):
            self.profile.settings = Profile.from_flat_list(self.profile.settings)

        for (section, setting_id), widget in self.widgets.items():
            value = self.profile.settings.get(section, {}).get(setting_id, None)
            
            # Get default value from widget if it was set during creation (for options)
            default_widget_value = None
            if isinstance(widget, customtkinter.CTkOptionMenu):
                default_widget_value = widget._values[0] if widget._values else "N/A"
            elif isinstance(widget, customtkinter.CTkEntry) and widget.get(): # if entry has placeholder/default
                pass # Keep placeholder if no profile value
            
            current_value_to_set = value if value is not None else default_widget_value

            if isinstance(widget, customtkinter.CTkEntry):
                widget.delete(0, "end")
                if current_value_to_set is not None: # only insert if there's a value
                    widget.insert(0, str(current_value_to_set))
            elif isinstance(widget, customtkinter.CTkOptionMenu):
                if current_value_to_set is not None and str(current_value_to_set) in widget._values:
                    widget.set(str(current_value_to_set))
                elif widget._values: # set to first option if value is invalid or not found
                    widget.set(widget._values[0])
            elif isinstance(widget, customtkinter.CTkTextbox):
                widget.delete("1.0", "end")
                if current_value_to_set is not None:
                    widget.insert("1.0", str(current_value_to_set))
    
    def _collect_data(self):
        """Collect data from widgets and update the profile object."""
        self.profile.name = self.name_entry.get()
        self.profile.description = self.desc_entry.get()
        
        new_settings = {}
        for (section, setting_id), widget in self.widgets.items():
            if section not in new_settings:
                new_settings[section] = {}
            
            value = None
            if isinstance(widget, customtkinter.CTkEntry):
                value = widget.get()
            elif isinstance(widget, customtkinter.CTkOptionMenu):
                value = widget.get()
            elif isinstance(widget, customtkinter.CTkTextbox):
                value = widget.get("1.0", "end-1c") # Get all text except trailing newline
            
            # Only save non-empty/non-default values if desired, or save all
            # For now, saving all collected values that are not None
            if value is not None and value != "": 
                new_settings[section][setting_id] = value
                
        self.profile.settings = new_settings
        
    def _on_save(self):
        """Handle the save action."""
        self._collect_data()
        if self.callback:
            # The profile object itself is modified, so callback receives the updated one
            self.callback(self.profile) 
        self.destroy()

# Example Usage (for testing purposes, not part of the module's direct execution)
if __name__ == '__main__':
    # This requires bios_profile.py to be in the same directory or accessible via PYTHONPATH
    # from bios_profile import Profile # Assuming it's in the same directory for this test

    root = customtkinter.CTk()
    root.title("Main Test Window")
    root.geometry("400x200")

    def open_editor_callback(returned_profile):
        print(f"Profile Editor Closed. Profile Name: {returned_profile.name}")
        print("Settings:")
        for section, settings_in_section in returned_profile.settings.items():
            print(f"  Section: {section}")
            for key, val in settings_in_section.items():
                print(f"    {key}: {val}")

    def open_new_profile_editor():
        # Create a dummy profile for testing
        new_profile = Profile(name="Test New Profile", description="A test profile created via UI.")
        # Optionally pre-populate some settings for testing _populate_fields
        # new_profile.settings = {
        #     "OC Tweaker": {"dramFrequency": "DDR5-7200", "memoryContextRestore": "Enabled"},
        #     "System Info": {"biosVersion": "TestBIOS 1.0"}
        # }
        editor = OclProfileEditor(root, mode='create', profile_obj=new_profile, callback=open_editor_callback)
        editor.mainloop()

    test_button = customtkinter.CTkButton(root, text="Open New Profile Editor", command=open_new_profile_editor)
    test_button.pack(pady=20)

    root.mainloop()
