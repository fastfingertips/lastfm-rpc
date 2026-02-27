import os
import customtkinter as ctk
from PIL import Image, ImageEnhance
from loguru import logger

from core.config import config
from constants.project import APP_NAME
from utils.dialogs import show_warning
from utils.i18n import messenger
from utils.urls import open_url

logger = logger.bind(name="gui")

class ConfigGUI:
    def __init__(self, current_config, on_save_callback):
        """
        Initializes the modern settings window using CustomTkinter.
        All settings are shown on a single scrollable page.
        """
        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} - {messenger('menu_settings')}")
        self.root.geometry("600x850")
        self.root.resizable(True, True)
        
        # Appearance settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config = current_config
        self.on_save = on_save_callback
        
        # Internal state to track unsaved changes during language switches
        self.temp_data = {}
        self.flag_images = {} # Cache for flag images

        self.setup_ui()

    def _clear_ui(self):
        """Clears all widgets from the root to allow rebuilding."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_lang_change(self, selected_lang):
        """Triggered when a flag icon is clicked."""
        if self.temp_data.get("lang") == selected_lang:
            return
            
        logger.info(f"Language changed to {selected_lang}, refreshing UI...")
        
        # 1. Capture current values from widgets before destroying them
        self._capture_current_values()
        
        # 2. Update config translations globally (temporarily for the GUI)
        new_translations = config._load_translations(selected_lang)
        if new_translations:
            config.translations = new_translations
            self.root.title(f"{APP_NAME} - {messenger('menu_settings')}")
        
        # 3. Update active lang in temp data
        self.temp_data["lang"] = selected_lang
        
        # 4. Rebuild the entire UI
        self._clear_ui()
        self.setup_ui()

    def _capture_current_values(self):
        """Saves values from widgets to temp_data."""
        try:
            self.temp_data = {
                "username": self.entry_username.get(),
                "api_key": self.entry_api_key.get(),
                "api_secret": self.entry_api_secret.get(),
                "details": self.entry_details.get(),
                "state": self.entry_state.get(),
                "small_image": self.check_small_image.get(),
                "scrobbles": self.check_scrobbles.get(),
                "focus": self.check_focus.get(),
                "lang": self.temp_data.get("lang", self.config.app_lang)
            }
        except Exception as e:
            logger.warning(f"Could not capture all values: {e}")

    def setup_ui(self):
        # Header Container (Title + Flags)
        header_container = ctk.CTkFrame(self.root, fg_color="transparent")
        header_container.pack(fill="x", padx=30, pady=(20, 0))

        # Title (Left aligned in header)
        ctk.CTkLabel(
            header_container, 
            text=messenger("gui_title"), 
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")

        # Flag Container (Right aligned in header)
        flag_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        flag_frame.pack(side="right")
        self._setup_flag_icons(flag_frame)

        # Main Scrollable Container
        self.scroll_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- SECTION: API & CONNECTION ---
        self._add_section_header("gui_tab_api", "Connection")
        
        self.entry_username = self.create_input(self.scroll_frame, messenger("gui_username"), self.temp_data.get("username", self.config.username))
        self.entry_api_key = self.create_input(self.scroll_frame, messenger("gui_api_key"), self.temp_data.get("api_key", self.config.api_key))
        self.entry_api_secret = self.create_input(self.scroll_frame, messenger("gui_api_secret"), self.temp_data.get("api_secret", self.config.api_secret), is_secret=True)
        
        # Help Links
        links_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        links_frame.pack(fill="x", pady=(5, 15))
        
        link1 = ctk.CTkLabel(links_frame, text="• " + messenger("gui_create_api"), text_color="#1f6aa5", cursor="hand2", font=ctk.CTkFont(size=12))
        link1.pack(anchor="w")
        link1.bind("<Button-1>", lambda e: open_url("https://www.last.fm/api/account/create"))

        link2 = ctk.CTkLabel(links_frame, text="• " + messenger("gui_view_apis"), text_color="#1f6aa5", cursor="hand2", font=ctk.CTkFont(size=12))
        link2.pack(anchor="w")
        link2.bind("<Button-1>", lambda e: open_url("https://www.last.fm/api/accounts"))

        self._add_separator()

        # --- SECTION: DISCORD RPC ---
        self._add_section_header("gui_tab_rpc", "Discord RPC")
        
        ctk.CTkLabel(self.scroll_frame, text="Text Templates", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 5))
        self.entry_details = self.create_input(self.scroll_frame, "Details Line", self.temp_data.get("details", self.config.rpc.details_template))
        self.entry_state = self.create_input(self.scroll_frame, "State Line", self.temp_data.get("state", self.config.rpc.state_template))

        # Placeholder help
        placeholder_text = (
            "Available: {title}, {artist}, {album}, {scrobbles}, {track_scrobbles}, {total_scrobbles}, {username}"
        )
        ctk.CTkLabel(self.scroll_frame, text=placeholder_text, font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", pady=(0, 15))

        # Display Toggles
        toggles_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", pady=5)
        
        self.check_small_image = self.create_switch(toggles_frame, messenger("menu_show_small_image"), self.temp_data.get("small_image", self.config.rpc.show_small_image))
        self.check_scrobbles = self.create_switch(toggles_frame, messenger("menu_show_scrobbles"), self.temp_data.get("scrobbles", self.config.rpc.show_scrobbles))
        self.check_focus = self.create_switch(toggles_frame, "Focus on Artist (Status Type)", self.temp_data.get("focus", self.config.rpc.focus_artist))

        self._add_separator()

        # --- SECTION: APPLICATION INFO ---
        self._add_section_header("gui_tab_app", "Info")
        from constants.project import VERSION
        ctk.CTkLabel(self.scroll_frame, text=f"Last.fm RPC v{VERSION}", font=ctk.CTkFont(size=12), text_color="gray50").pack(anchor="w")

        # --- FOOTER BUTTONS ---
        footer_frame = ctk.CTkFrame(self.root, fg_color="transparent", height=60)
        footer_frame.pack(fill="x", side="bottom", padx=30, pady=20)

        self.save_btn = ctk.CTkButton(
            footer_frame, 
            text=messenger("gui_save_btn"), 
            command=self.save,
            font=ctk.CTkFont(weight="bold"),
            height=40
        )
        self.save_btn.pack(side="right", padx=5)

        self.cancel_btn = ctk.CTkButton(
            footer_frame, 
            text="Cancel", 
            fg_color="gray30",
            hover_color="gray40",
            command=self.root.destroy,
            height=40
        )
        self.cancel_btn.pack(side="right", padx=5)

    def _setup_flag_icons(self, parent):
        """Creates clickable flag icons for language selection."""
        current_lang = self.temp_data.get("lang", self.config.app_lang)
        flag_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "flags")
        
        # Languages we support with flags
        langs = ["tr-TR", "en-US", "es-ES"]
        
        for lang in langs:
            flag_path = os.path.join(flag_dir, f"{lang}.png")
            if not os.path.exists(flag_path):
                continue
                
            try:
                # Load or reuse image
                img = Image.open(flag_path).convert("RGBA")
                
                # If not the current language, make it faded (low saturation and opacity)
                if lang != current_lang:
                    # Desaturate
                    converter = ImageEnhance.Color(img)
                    img = converter.enhance(0.2)
                    # Dim it a bit
                    brightness = ImageEnhance.Brightness(img)
                    img = brightness.enhance(0.6)
                
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(30, 20))
                
                # Create button-like label
                btn = ctk.CTkLabel(parent, image=ctk_img, text="", cursor="hand2")
                btn.pack(side="left", padx=5)
                
                # Bind click event
                btn.bind("<Button-1>", lambda e, l=lang: self.on_lang_change(l))
                
                # Add tooltip-like hover effect (optional, just text color change if we had labels)
                if lang == current_lang:
                    # Add a small highlight underline
                    underline = ctk.CTkFrame(parent, height=2, width=30, fg_color="#1f6aa5")
                    # This is tricky with pack, so we just use border/padding logic if needed
                
            except Exception as e:
                logger.error(f"Error loading flag {lang}: {e}")

    def _add_section_header(self, messenger_key, fallback):
        text = messenger(messenger_key)
        if text == messenger_key:
            text = fallback
        
        ctk.CTkLabel(
            self.scroll_frame, 
            text=text.upper(), 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f6aa5"
        ).pack(anchor="w", pady=(10, 10))

    def _add_separator(self):
        ctk.CTkFrame(self.scroll_frame, height=2, fg_color="gray25").pack(fill="x", pady=20)

    def create_input(self, parent, label_text, current_val, is_secret=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=13)).pack(anchor="w")
        
        clean_val = str(current_val) if not str(current_val).startswith("<") else ""
        entry = ctk.CTkEntry(frame, placeholder_text=label_text, show="*" if is_secret else "", height=35)
        entry.insert(0, clean_val)
        entry.pack(fill="x", pady=(2, 0))
        return entry

    def create_switch(self, parent, text, initial_state):
        switch_var = ctk.BooleanVar(value=initial_state)
        switch = ctk.CTkSwitch(parent, text=text, variable=switch_var)
        switch.pack(anchor="w", pady=8)
        return switch_var

    def save(self):
        self._capture_current_values()
        u = self.temp_data["username"].strip()
        k = self.temp_data["api_key"].strip()
        s = self.temp_data["api_secret"].strip()
        lang = self.temp_data["lang"]

        rpc_data = {
            "DETAILS_TEMPLATE": self.temp_data["details"].strip(),
            "STATE_TEMPLATE": self.temp_data["state"].strip(),
            "SHOW_SMALL_IMAGE": self.temp_data["small_image"],
            "SHOW_SCROBBLES": self.temp_data["scrobbles"],
            "FOCUS_ARTIST": self.temp_data["focus"],
        }

        if not all([u, k, s]):
            show_warning(messenger("gui_warning_title"), messenger("gui_warning_body"))
            return

        if self.on_save({"USER": {"USERNAME": u}, "API": {"KEY": k, "SECRET": s}, "APP": {"LANG": lang}, "RPC": rpc_data}):
            self.root.destroy()

    def run(self):
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        self.root.mainloop()
