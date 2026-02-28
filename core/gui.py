import os

import customtkinter as ctk
from loguru import logger
from PIL import Image, ImageEnhance

from constants.project import APP_NAME
from core.config import config
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
        self.root.geometry("620x820")
        self.root.resizable(True, True)

        # Appearance settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config = current_config
        self.on_save = on_save_callback

        # Internal state to track unsaved changes during language switches
        self.temp_data = {}
        self.flag_images = {}  # Cache for flag images

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
                "large_text": self.entry_large_text.get(),
                "small_text": self.entry_small_text.get(),
                "large_image": self.entry_large_image.get(),
                "small_image_url": self.entry_small_image_url.get(),
                "small_image": bool(self.check_small_image.get()),
                "scrobbles": bool(self.check_scrobbles.get()),
                "focus": bool(self.check_focus.get()),
                "custom_large_img": bool(self.check_custom_large_img.get()),
                "custom_large_txt": bool(self.check_custom_large_txt.get()),
                "custom_small_img": bool(self.check_custom_small_img.get()),
                "custom_small_txt": bool(self.check_custom_small_txt.get()),
                "auto_start": bool(self.check_auto_start.get()),
                "lang": self.temp_data.get("lang", self.config.app_lang),
                "button_1": self.entry_button_1.get(),
                "button_2": self.entry_button_2.get(),
            }
        except Exception as e:
            logger.warning(f"Could not capture all values: {e}")

    def setup_ui(self):
        """Builds the entire settings interface."""
        self._setup_header()

        # Main Scrollable Container
        self.scroll_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Build individual sections
        self._setup_api_section()
        self._add_separator()
        self._setup_text_section()
        self._setup_image_section()
        self._setup_button_section()
        self._setup_toggle_section()

        self._setup_footer()

        # Initial toggle state update
        self._update_toggle_states()

    def _setup_header(self):
        """Header Container (Title + Flags)"""
        header_container = ctk.CTkFrame(self.root, fg_color="transparent")
        header_container.pack(fill="x", padx=30, pady=(20, 0))

        # Title
        ctk.CTkLabel(header_container, text=messenger("gui_title"), font=ctk.CTkFont(size=24, weight="bold")).pack(
            side="left"
        )

        # Flag Container
        flag_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        flag_frame.pack(side="right")
        self._setup_flag_icons(flag_frame)

    def _setup_api_section(self):
        """SECTION: API & CONNECTION"""
        self._add_section_header("gui_tab_api", "Connection")

        api_split = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        api_split.pack(fill="x")

        self.entry_username = self.create_input(
            api_split, messenger("gui_username"), self.temp_data.get("username", self.config.username)
        )
        self.entry_username.master.pack(side="left", expand=True, fill="x", padx=(0, 5))  # type: ignore

        self.entry_api_key = self.create_input(
            api_split, messenger("gui_api_key"), self.temp_data.get("api_key", self.config.api_key)
        )
        self.entry_api_key.master.pack(side="left", expand=True, fill="x", padx=(5, 0))  # type: ignore

        self.entry_api_secret = self.create_input(
            self.scroll_frame,
            messenger("gui_api_secret"),
            self.temp_data.get("api_secret", self.config.api_secret),
            is_secret=True,
        )

        # Help Links
        links_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        links_frame.pack(fill="x", pady=(5, 15))

        link_data = [
            (messenger("gui_create_api"), "https://www.last.fm/api/account/create"),
            (messenger("gui_view_apis"), "https://www.last.fm/api/accounts"),
        ]

        for text, url in link_data:
            lbl = ctk.CTkLabel(
                links_frame, text=f"• {text}", text_color="#1f6aa5", cursor="hand2", font=ctk.CTkFont(size=12)
            )
            lbl.pack(anchor="w")
            lbl.bind("<Button-1>", lambda e, u=url: open_url(u))

    def _setup_text_section(self):
        """SECTION: DISCORD RPC - TEXT OVERRIDES"""
        self._add_section_header("gui_tab_rpc", "Discord RPC")

        ctk.CTkLabel(
            self.scroll_frame, text="TEXT TEMPLATES", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60"
        ).pack(anchor="w", pady=(5, 5))

        ds_row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        ds_row.pack(fill="x")
        self.entry_details = self.create_input(
            ds_row, "Details Line (1st)", self.temp_data.get("details", self.config.rpc.details_template)
        )
        self.entry_details.master.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.entry_state = self.create_input(
            ds_row, "State Line (2nd)", self.temp_data.get("state", self.config.rpc.state_template)
        )
        self.entry_state.master.pack(side="left", expand=True, fill="x", padx=(5, 0))

        hover_row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        hover_row.pack(fill="x", pady=(5, 0))
        self.entry_large_text = self.create_input(
            hover_row, "Large Hover Text (3rd)", self.temp_data.get("large_text", self.config.rpc.large_text_template)
        )
        self.entry_large_text.master.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.entry_small_text = self.create_input(
            hover_row, "Small Hover Text (4th)", self.temp_data.get("small_text", self.config.rpc.small_text_template)
        )
        self.entry_small_text.master.pack(side="left", expand=True, fill="x", padx=(5, 0))

        txt_toggles = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        txt_toggles.pack(fill="x")
        self.check_custom_large_txt = self.create_switch(
            txt_toggles,
            "Custom Large Text",
            self.temp_data.get("custom_large_txt", self.config.rpc.use_custom_large_text),
            command=self._update_toggle_states,
        )
        self.check_custom_large_txt.pack(side="left", expand=True, fill="x")
        self.check_custom_small_txt = self.create_switch(
            txt_toggles,
            "Custom Small Text",
            self.temp_data.get("custom_small_txt", self.config.rpc.use_custom_small_text),
            command=self._update_toggle_states,
        )
        self.check_custom_small_txt.pack(side="left", expand=True, fill="x")

    def _setup_image_section(self):
        """SECTION: IMAGE SOURCES"""
        ctk.CTkLabel(
            self.scroll_frame, text="IMAGE SOURCES", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60"
        ).pack(anchor="w", pady=(15, 5))

        img_row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        img_row.pack(fill="x")
        self.entry_large_image = self.create_input(
            img_row, "Large Image URL", self.temp_data.get("large_image", self.config.rpc.large_image_template)
        )
        self.entry_large_image.master.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.entry_small_image_url = self.create_input(
            img_row, "Small Image URL", self.temp_data.get("small_image_url", self.config.rpc.small_image_template)
        )
        self.entry_small_image_url.master.pack(side="left", expand=True, fill="x", padx=(5, 0))

        img_toggles = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        img_toggles.pack(fill="x")
        self.check_custom_large_img = self.create_switch(
            img_toggles,
            "Custom Large URL",
            self.temp_data.get("custom_large_img", self.config.rpc.use_custom_large_image),
            command=self._update_toggle_states,
        )
        self.check_custom_large_img.pack(side="left", expand=True, fill="x")
        self.check_custom_small_img = self.create_switch(
            img_toggles,
            "Custom Small URL",
            self.temp_data.get("custom_small_img", self.config.rpc.use_custom_small_image),
            command=self._update_toggle_states,
        )
        self.check_custom_small_img.pack(side="left", expand=True, fill="x")

        placeholder_text = "Available: {title}, {artist}, {album}, {scrobbles}, {username}, {avatar_url}, {artwork_url}"
        ctk.CTkLabel(self.scroll_frame, text=placeholder_text, font=ctk.CTkFont(size=10), text_color="gray50").pack(
            anchor="w", pady=(5, 10)
        )

    def _setup_button_section(self):
        """SECTION: INTERACTIVE BUTTONS"""
        ctk.CTkLabel(
            self.scroll_frame, text="INTERACTIVE BUTTONS", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60"
        ).pack(anchor="w", pady=(15, 5))

        btn_row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        button_options = ["lastfm_track", "lastfm_user_track", "lastfm_profile", "youtube", "spotify", "none"]

        # Button 1 Dropdown
        btn1_frame = ctk.CTkFrame(btn_row, fg_color="transparent")
        btn1_frame.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkLabel(btn1_frame, text="Button 1 Action", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_button_1 = ctk.CTkOptionMenu(btn1_frame, values=button_options, height=32)
        self.entry_button_1.set(self.temp_data.get("button_1", self.config.rpc.button_1))
        self.entry_button_1.pack(fill="x", pady=(1, 0))

        # Button 2 Dropdown
        btn2_frame = ctk.CTkFrame(btn_row, fg_color="transparent")
        btn2_frame.pack(side="left", expand=True, fill="x", padx=(5, 0))
        ctk.CTkLabel(btn2_frame, text="Button 2 Action", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_button_2 = ctk.CTkOptionMenu(btn2_frame, values=button_options, height=32)
        self.entry_button_2.set(self.temp_data.get("button_2", self.config.rpc.button_2))
        self.entry_button_2.pack(fill="x", pady=(1, 0))

    def _setup_toggle_section(self):
        """SECTION: DISPLAY TOGGLES"""
        toggles_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        toggles_container.pack(fill="x", pady=5)

        tr1 = ctk.CTkFrame(toggles_container, fg_color="transparent")
        tr1.pack(fill="x")
        self.check_small_image = self.create_switch(
            tr1, messenger("menu_show_small_image"), self.temp_data.get("small_image", self.config.rpc.show_small_image)
        )
        self.check_small_image.pack(side="left", expand=True, fill="x")
        self.check_scrobbles = self.create_switch(
            tr1, messenger("menu_show_scrobbles"), self.temp_data.get("scrobbles", self.config.rpc.show_scrobbles)
        )
        self.check_scrobbles.pack(side="left", expand=True, fill="x")

        tr2 = ctk.CTkFrame(toggles_container, fg_color="transparent")
        tr2.pack(fill="x")
        self.check_focus = self.create_switch(
            tr2, "Focus on Artist", self.temp_data.get("focus", self.config.rpc.focus_artist)
        )
        self.check_focus.pack(side="left", expand=True, fill="x")
        self.check_auto_start = self.create_switch(
            tr2, messenger("menu_auto_start"), self.temp_data.get("auto_start", self.config.auto_start_enabled)
        )
        self.check_auto_start.pack(side="left", expand=True, fill="x")

        from constants.project import VERSION

        ctk.CTkLabel(
            self.scroll_frame, text=f"Last.fm RPC v{VERSION}", font=ctk.CTkFont(size=12), text_color="gray40"
        ).pack(anchor="e", pady=(0, 10))

    def _setup_footer(self):
        """Footer BUTTONS"""
        footer_frame = ctk.CTkFrame(self.root, fg_color="transparent", height=60)
        footer_frame.pack(fill="x", side="bottom", padx=30, pady=20)

        self.save_btn = ctk.CTkButton(
            footer_frame, text=messenger("gui_save_btn"), command=self.save, font=ctk.CTkFont(weight="bold"), height=40
        )
        self.save_btn.pack(side="right", padx=5)

        self.cancel_btn = ctk.CTkButton(
            footer_frame, text="Cancel", fg_color="gray30", hover_color="gray40", command=self.root.destroy, height=40
        )
        self.cancel_btn.pack(side="right", padx=5)

    def _update_toggle_states(self):
        """Disables individual toggles if custom templates are enabled for that specific feature."""
        is_custom_small_txt = self.check_custom_small_txt.get()

        # Scrobbles toggle only affects Small Text (Automated)
        self.check_scrobbles.configure(state="disabled" if is_custom_small_txt else "normal")
        self.check_scrobbles.configure(text_color="gray40" if is_custom_small_txt else "white")

        # In this simplistic design, we don't have Automated toggles for Large Text yet
        # (other than the Radio button in Tray), but we can dim the inputs if needed.
        # However, it's better to keep the input always enabled for editing.

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
                btn.bind("<Button-1>", lambda e, lang_code=lang: self.on_lang_change(lang_code))

                # Add tooltip-like hover effect (optional, just text color change if we had labels)
                if lang == current_lang:
                    # Add a small highlight underline
                    ctk.CTkFrame(parent, height=2, width=30, fg_color="#1f6aa5")
                    # This is tricky with pack, so we just use border/padding logic if needed

            except Exception as e:
                logger.error(f"Error loading flag {lang}: {e}")

    def _add_section_header(self, messenger_key, fallback):
        text = messenger(messenger_key)
        if text == messenger_key:
            text = fallback

        ctk.CTkLabel(
            self.scroll_frame, text=text.upper(), font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f6aa5"
        ).pack(anchor="w", pady=(10, 10))

    def _add_separator(self):
        ctk.CTkFrame(self.scroll_frame, height=2, fg_color="gray25").pack(fill="x", pady=20)

    def create_input(self, parent, label_text, current_val, is_secret=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        # Don't pack immediately if we want to pack with different settings
        frame.pack(fill="x", pady=4)

        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12)).pack(anchor="w")

        clean_val = str(current_val) if not str(current_val).startswith("<") else ""
        entry = ctk.CTkEntry(frame, placeholder_text=label_text, show="*" if is_secret else "", height=32)
        entry.insert(0, clean_val)
        entry.pack(fill="x", pady=(1, 0))
        return entry

    def create_switch(self, parent, text, initial_state, command=None):
        switch_var = ctk.BooleanVar(value=initial_state)
        switch = ctk.CTkSwitch(parent, text=text, variable=switch_var, command=command, font=ctk.CTkFont(size=12))
        switch.pack(anchor="w", pady=4)
        return switch

    def save(self):
        self._capture_current_values()
        u = self.temp_data["username"].strip()
        k = self.temp_data["api_key"].strip()
        s = self.temp_data["api_secret"].strip()
        lang_val = self.temp_data["lang"]
        a = self.temp_data["auto_start"]

        rpc_data = {
            "details_template": self.temp_data["details"].strip(),
            "state_template": self.temp_data["state"].strip(),
            "large_text_template": self.temp_data["large_text"].strip(),
            "small_text_template": self.temp_data["small_text"].strip(),
            "large_image_template": self.temp_data["large_image"].strip(),
            "small_image_template": self.temp_data["small_image_url"].strip(),
            "show_small_image": self.temp_data["small_image"],
            "show_scrobbles": self.temp_data["scrobbles"],
            "focus_artist": self.temp_data["focus"],
            "use_custom_large_image": self.temp_data["custom_large_img"],
            "use_custom_large_text": self.temp_data["custom_large_txt"],
            "use_custom_small_image": self.temp_data["custom_small_img"],
            "use_custom_small_text": self.temp_data["custom_small_txt"],
            "button_1": self.temp_data.get("button_1", "lastfm_track"),
            "button_2": self.temp_data.get("button_2", "youtube"),
        }

        if not all([u, k, s]):
            show_warning(messenger("gui_warning_title"), messenger("gui_warning_body"))
            return

        if self.on_save(
            {
                "USER": {"USERNAME": u},
                "API": {"KEY": k, "SECRET": s},
                "APP": {"LANG": lang_val, "AUTO_START": a},
                "RPC": rpc_data,
            }
        ):
            # visual feedback instead of closing
            original_text = self.save_btn.cget("text")
            original_color = self.save_btn.cget("fg_color")

            self.save_btn.configure(text="Saved!", fg_color="#28a745")
            self.root.after(1500, lambda: self.save_btn.configure(text=original_text, fg_color=original_color))

    def run(self):
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.root.mainloop()
