# ocl_module_src/profile_editor_ui.py
# Author: System Sage
# Date: 06/18/2025
# Description: Provides a comprehensive GUI for creating and editing detailed BIOS
#              profiles, replacing the need for manual dialog-based entry.

import customtkinter as ctk
from tkinter import ttk
from tkinterweb import HtmlFrame
from ocl_module_src.bios_profile import Profile

class OclProfileEditor(ctk.CTkToplevel):
    def __init__(self, master, profile: Profile, callback=None):
        super().__init__(master)
        self.title("OCL Profile Editor")
        self.geometry("1000x800")
        self.profile = profile
        self.callback = callback
        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.create_widgets()
        
        self.grab_set() # Make this window modal
        # No cancel or save button; only HTML reference tab is available.
        
        self.focus_set() # Set focus to this window

    def create_widgets(self):
        # Only show the HTML reference tab for now. All legacy/dynamic UI code is removed due to data model refactor.
        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        self.notebook.add('Reference HTML')
        self.create_reference_html_tab(self.notebook.tab('Reference HTML'))
    def create_reference_html_tab(self, parent_tab):
        """
        Display a minimal HTML string to test if tkinterweb is working at all.
        """
        frame = ctk.CTkFrame(parent_tab)
        frame.pack(expand=True, fill="both")
        html_view = HtmlFrame(frame, horizontal_scrollbar="auto")
        html_view.pack(expand=True, fill="both")
        try:
            html_view.load_html("<h2 style='color:green'>tkinterweb is working!<br>This is a minimal HTML test.</h2><p>If you see this, tkinterweb is functional. If not, tkinterweb is not working in your environment.</p>")
            print("[DEBUG] Minimal HTML loaded in tkinterweb.")
        except Exception as e:
            print(f"[ERROR] tkinterweb load_html failed: {e}")

        # No action buttons for now; only HTML reference is shown.


    # All legacy/dynamic UI code is removed for now. Only the HTML reference tab is available.


if __name__ == '__main__':
    # This is for testing purposes
    root = ctk.CTk()
    root.title("Profile Editor Test")
    
    # Create a dummy profile for testing
    dummy_profile = Profile(name="Test Profile")
    
    def test_callback(profile):
        print("--- Callback Received ---")
        print(f"Profile Name: {profile.name}")
        print(f"Description: {profile.description}")
        print(f"CPU Ratio: {profile.oc_tweaker.cpu_ratio}")
        root.quit()

    def open_editor():
        editor = OclProfileEditor(root, profile=dummy_profile, callback=test_callback)
        editor.grab_set()

    open_button = ctk.CTkButton(root, text="Open Editor", command=open_editor)
    open_button.pack(padx=20, pady=20)
    
    root.mainloop()
