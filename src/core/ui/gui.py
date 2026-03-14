import os
import threading

import customtkinter as ctk
from loguru import logger
from PIL import Image, ImageEnhance

from constants.project import APP_NAME, VERSION
from core.ui.gui_components import GuiComponents
from utils.app.i18n import i18n, messenger
from utils.core.paths import get_asset_path
from utils.gui.dialogs import show_warning
from utils.net.urls import open_url

logger = logger.bind(name="gui")


class ConfigGUI:
    @staticmethod
    def launch(current_config, on_save_callback, is_wizard=False):
        """Helper to create and run the GUI instance."""
        gui = ConfigGUI(current_config, on_save_callback, is_wizard=is_wizard)

        def on_close():
            gui.root.quit()
            gui.root.destroy()

        gui.root.protocol("WM_DELETE_WINDOW", on_close)
        gui.run()

    def __init__(self, current_config, on_save_callback, is_wizard=False):
        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} - {messenger('menu_settings')}")
        self.is_wizard = is_wizard

        if is_wizard:
            self.root.geometry("480x560")
        else:
            self.root.geometry("620x820")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config = current_config
        self.on_save = on_save_callback

        # Temporary storage for fields
        self.fields = {}
        self.temp_values = {}  # Used for lang switching

        self.setup_ui()

    def _capture_to_temp(self):
        """Captures all current widget values into temp_values."""
        self.temp_values = {k: v.get() if hasattr(v, "get") else v for k, v in self.fields.items()}
        # Handle special cases if any
        if "lang" not in self.temp_values:
            self.temp_values["lang"] = self.config.app_lang

    def on_lang_change(self, selected_lang):
        if self.temp_values.get("lang") == selected_lang:
            return

        self._capture_to_temp()
        self.temp_values["lang"] = selected_lang

        # Load new translations via i18n manager
        i18n.load(selected_lang)
        self.root.title(f"{APP_NAME} - {messenger('menu_settings')}")

        # Rebuild UI
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()

    def setup_ui(self):
        self._setup_header()

        scroll = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Content Sections
        self._build_api_section(scroll)

        if not self.is_wizard:
            GuiComponents.create_separator(scroll)
            self._build_rpc_text_section(scroll)
            self._build_rpc_image_section(scroll)
            self._build_button_section(scroll)
            self._build_toggle_section(scroll)
        else:
            # In wizard mode, add a small helpful note
            ctk.CTkLabel(
                scroll,
                text="Advanced settings will be available in the system tray later.",
                font=ctk.CTkFont(slant="italic", size=11),
                text_color="gray",
            ).pack(pady=20)

        self._setup_footer()

    def _setup_header(self):
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 0))

        ctk.CTkLabel(header, text=messenger("gui_title"), font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        # Flags
        flag_frame = ctk.CTkFrame(header, fg_color="transparent")
        flag_frame.pack(side="right")
        self._draw_flags(flag_frame)

    def _build_api_section(self, scroll):
        GuiComponents.create_section_header(scroll, "gui_tab_api", "Connection")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x")

        self.fields["username"] = GuiComponents.create_input(
            row, messenger("gui_username"), self.temp_values.get("username", self.config.username)
        )
        self.fields["username"].master.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.fields["api_key"] = GuiComponents.create_input(
            row, messenger("gui_api_key"), self.temp_values.get("api_key", self.config.api_key)
        )
        self.fields["api_key"].master.pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.fields["api_secret"] = GuiComponents.create_input(
            scroll,
            messenger("gui_api_secret"),
            self.temp_values.get("api_secret", self.config.api_secret),
            is_secret=True,
        )

        # Links
        links = ctk.CTkFrame(scroll, fg_color="transparent")
        links.pack(fill="x", pady=(5, 10))
        for text_key, url in [
            ("gui_create_api", "https://www.last.fm/api/account/create"),
            ("gui_view_apis", "https://www.last.fm/api/accounts"),
        ]:
            lbl = ctk.CTkLabel(
                links, text=f"• {messenger(text_key)}", text_color="#1f6aa5", cursor="hand2", font=ctk.CTkFont(size=12)
            )
            lbl.pack(anchor="w")
            lbl.bind("<Button-1>", lambda e, u=url: open_url(u))

        self.test_btn = GuiComponents.create_button(
            scroll, messenger("gui_test_conn_btn"), self._test_connection, fg_color="gray30", hover_color="gray40"
        )

        # Config Path Display
        config_path = self.config.config_path
        path_label = ctk.CTkLabel(
            scroll,
            text=messenger("gui_config_path", config_path),
            font=ctk.CTkFont(size=10),
            text_color="gray50",
            cursor="hand2",
        )
        path_label.pack(anchor="w", pady=(10, 0))
        path_label.bind("<Button-1>", lambda e: open_url(os.path.dirname(config_path)))

    def _build_rpc_text_section(self, scroll):
        GuiComponents.create_section_header(scroll, "gui_tab_rpc", "Discord RPC")

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x")
        self.fields["details"] = GuiComponents.create_input(
            row1, "Details Template", self.temp_values.get("details", self.config.rpc.details_template)
        )
        self.fields["details"].master.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.fields["state"] = GuiComponents.create_input(
            row1, "State Template", self.temp_values.get("state", self.config.rpc.state_template)
        )
        self.fields["state"].master.pack(side="left", expand=True, fill="x", padx=(5, 0))

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        self.fields["large_text"] = GuiComponents.create_input(
            row2, "Large Hover Text", self.temp_values.get("large_text", self.config.rpc.large_text_template)
        )
        self.fields["large_text"].master.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.fields["small_text"] = GuiComponents.create_input(
            row2, "Small Hover Text", self.temp_values.get("small_text", self.config.rpc.small_text_template)
        )
        self.fields["small_text"].master.pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _build_rpc_image_section(self, scroll):
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=10)
        self.fields["large_image"] = GuiComponents.create_input(
            row, "Large Image URL", self.temp_values.get("large_image", self.config.rpc.large_image_template)
        )
        self.fields["large_image"].master.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.fields["small_image_url"] = GuiComponents.create_input(
            row, "Small Image URL", self.temp_values.get("small_image_url", self.config.rpc.small_image_template)
        )
        self.fields["small_image_url"].master.pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _build_button_section(self, scroll):
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=10)
        opts = ["lastfm_track", "lastfm_user_track", "lastfm_profile", "youtube", "spotify", "none"]

        for i, key in enumerate(["button_1", "button_2"], 1):
            f = ctk.CTkFrame(row, fg_color="transparent")
            f.pack(side="left", expand=True, fill="x", padx=(0 if i == 1 else 5, 5 if i == 1 else 0))
            ctk.CTkLabel(f, text=f"Button {i} Action", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.fields[key] = ctk.CTkOptionMenu(f, values=opts, height=32)
            self.fields[key].set(self.temp_values.get(key, getattr(self.config.rpc, key)))
            self.fields[key].pack(fill="x", pady=2)

    def _build_toggle_section(self, scroll):
        # We use a mapping to build these quickly
        switches = [
            ("small_image", messenger("menu_show_small_image"), self.config.rpc.show_small_image),
            ("scrobbles", messenger("menu_show_scrobbles"), self.config.rpc.show_scrobbles),
            ("focus", "Focus on Artist", self.config.rpc.focus_artist),
            ("auto_start", messenger("menu_auto_start"), self.config.auto_start_enabled),
            ("custom_large_img", "Custom Large URL", self.config.rpc.use_custom_large_image),
            ("custom_small_img", "Custom Small URL", self.config.rpc.use_custom_small_image),
            ("custom_large_txt", "Custom Large Text", self.config.rpc.use_custom_large_text),
            ("custom_small_txt", "Custom Small Text", self.config.rpc.use_custom_small_text),
        ]

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        for i, (key, label, default) in enumerate(switches):
            s, var = GuiComponents.create_switch(grid, label, self.temp_values.get(key, default), pack=False)
            s.grid(row=i // 2, column=i % 2, sticky="w", padx=20, pady=5)
            self.fields[key] = var

        ctk.CTkLabel(scroll, text=f"Last.fm RPC v{VERSION}", font=ctk.CTkFont(size=12), text_color="gray40").pack(
            anchor="e", pady=10
        )

    def _setup_footer(self):
        footer = ctk.CTkFrame(self.root, fg_color="transparent", height=60)
        footer.pack(fill="x", side="bottom", padx=30, pady=20)

        self.save_btn = ctk.CTkButton(
            footer, text=messenger("gui_save_btn"), command=self.save, font=ctk.CTkFont(weight="bold"), height=40
        )
        self.save_btn.pack(side="right", padx=5)
        ctk.CTkButton(
            footer, text="Cancel", fg_color="gray30", hover_color="gray40", command=self.root.destroy, height=40
        ).pack(side="right", padx=5)

    def _draw_flags(self, parent):
        curr = self.temp_values.get("lang", self.config.app_lang)
        for lang in ["tr-TR", "en-US", "es-ES"]:
            path = get_asset_path(os.path.join("flags", f"{lang}.png"))
            if not os.path.exists(path):
                continue
            img = Image.open(path).convert("RGBA")
            if lang != curr:
                img = ImageEnhance.Color(img).enhance(0.2)
                img = ImageEnhance.Brightness(img).enhance(0.6)
            ctk_img = ctk.CTkImage(img, size=(30, 20))
            btn = ctk.CTkLabel(parent, image=ctk_img, text="", cursor="hand2")
            btn.pack(side="left", padx=5)
            btn.bind("<Button-1>", lambda e, lang_code=lang: self.on_lang_change(lang_code))

    def _test_connection(self):
        """Validates API credentials asynchronously."""
        username = self.fields["username"].get()
        api_key = self.fields["api_key"].get()
        api_secret = self.fields["api_secret"].get()

        if not all([username, api_key, api_secret]):
            show_warning(messenger("gui_warning_title"), messenger("gui_warning_body"))
            return

        self.test_btn.configure(text=messenger("gui_test_conn_testing"), state="disabled")

        def run_test():
            import pylast

            try:
                network = pylast.LastFMNetwork(api_key, api_secret)
                user = network.get_user(username)
                # Calling get_name() on the user object forces a small API call to verify existence and key validity
                user.get_name()

                self.root.after(
                    0,
                    lambda: self.test_btn.configure(
                        text=messenger("gui_test_conn_success"), fg_color="#28a745", state="normal"
                    ),
                )
            except Exception as e:
                error_msg = str(e)
                self.root.after(
                    0,
                    lambda: self.test_btn.configure(
                        text=messenger("gui_test_conn_btn"), fg_color="gray30", state="normal"
                    ),
                )
                self.root.after(0, lambda: show_warning(messenger("err"), messenger("gui_test_conn_error", error_msg)))
            finally:
                # Reset button color after a delay if successful
                if "success" in self.test_btn.cget("text").lower() or "başarılı" in self.test_btn.cget("text").lower():
                    self.root.after(3000, lambda: self.test_btn.configure(fg_color="gray30"))

        threading.Thread(target=run_test, daemon=True).start()

    def save(self):
        self._capture_to_temp()
        d = self.temp_values

        # Validation for required fields
        if not all([d.get("username"), d.get("api_key"), d.get("api_secret")]):
            show_warning(messenger("gui_warning_title"), messenger("gui_warning_body"))
            return

        payload = {
            "USER": {"USERNAME": d.get("username")},
            "API": {"KEY": d.get("api_key"), "SECRET": d.get("api_secret")},
            "APP": {
                "LANG": d.get("lang", self.config.app_lang),
                "AUTO_START": d.get("auto_start", self.config.auto_start_enabled),
            },
            "RPC": {},
        }

        # Mapping for RPC fields that might be present
        rpc_mapping = {
            "small_image": "show_small_image",
            "scrobbles": "show_scrobbles",
            "focus": "focus_artist",
            "details": "details_template",
            "state": "state_template",
            "large_text": "large_text_template",
            "small_text": "small_text_template",
            "large_image": "large_image_template",
            "small_image_url": "small_image_template",
            "custom_large_img": "use_custom_large_image",
            "custom_small_img": "use_custom_small_image",
            "custom_large_txt": "use_custom_large_text",
            "custom_small_txt": "use_custom_small_text",
            "button_1": "button_1",
            "button_2": "button_2",
        }

        for temp_key, rpc_key in rpc_mapping.items():
            if temp_key in d:
                payload["RPC"][rpc_key] = d[temp_key]

        if self.on_save(payload):
            self.save_btn.configure(text="Saved!", fg_color="#28a745")
            self.root.after(1500, lambda: self.save_btn.configure(text=messenger("gui_save_btn"), fg_color="#1f6aa5"))

    def run(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        self.root.mainloop()
