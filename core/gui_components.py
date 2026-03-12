import customtkinter as ctk

from utils.i18n import messenger


class GuiComponents:
    """Helper to create consistent UI components for the settings windnow."""

    @staticmethod
    def create_section_header(parent, messenger_key, fallback):
        text = messenger(messenger_key)
        if text == messenger_key:
            text = fallback

        lbl = ctk.CTkLabel(parent, text=text.upper(), font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f6aa5")
        lbl.pack(anchor="w", pady=(15, 10))
        return lbl

    @staticmethod
    def create_input(parent, label_text, current_val, is_secret=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=4)

        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12)).pack(anchor="w")

        # Strip placeholders
        clean_val = str(current_val) if not str(current_val).startswith("<") else ""
        entry = ctk.CTkEntry(frame, placeholder_text=label_text, show="*" if is_secret else "", height=32)
        entry.insert(0, clean_val)
        entry.pack(fill="x", pady=(1, 0))
        return entry

    @staticmethod
    def create_switch(parent, text, initial_state, command=None):
        switch_var = ctk.BooleanVar(value=initial_state)
        switch = ctk.CTkSwitch(parent, text=text, variable=switch_var, command=command, font=ctk.CTkFont(size=12))
        switch.pack(anchor="w", pady=4)
        return switch, switch_var

    @staticmethod
    def create_separator(parent):
        sep = ctk.CTkFrame(parent, height=2, fg_color="gray25")
        sep.pack(fill="x", pady=20)
        return sep
