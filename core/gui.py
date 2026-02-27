import os
import tkinter as tk
from tkinter import ttk

# Ensure absolute paths if needed, but constants handle paths
from constants.project import APP_NAME, TRANSLATIONS_DIR
from utils.dialogs import show_warning
from utils.i18n import messenger
from utils.urls import open_url


class ConfigGUI:
    def __init__(self, current_config_values, on_save_callback):
        """
        Initializes a simple settings window.
        """
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - {messenger('menu_settings')}")
        self.root.geometry("400x480")
        self.root.resizable(False, False)

        self.current_config = current_config_values
        self.on_save = on_save_callback

        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text=messenger("gui_title"), font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))

        # API Key
        self.entry_api_key = self.create_input(main_frame, messenger("gui_api_key"), self.current_config[1])
        # API Secret
        self.entry_api_secret = self.create_input(
            main_frame, messenger("gui_api_secret"), self.current_config[2], is_secret=True
        )
        # Username
        self.entry_username = self.create_input(main_frame, messenger("gui_username"), self.current_config[0])

        # Language
        tk.Label(main_frame, text=messenger("gui_app_lang")).pack(anchor="w", pady=(10, 0))
        self.lang_var = tk.StringVar(value=self.current_config[3])
        try:
            available_langs = [f.replace(".yaml", "") for f in os.listdir(TRANSLATIONS_DIR) if f.endswith(".yaml")]
        except Exception:
            available_langs = ["en-US"]

        self.lang_combo = ttk.Combobox(main_frame, textvariable=self.lang_var, values=available_langs, state="readonly")
        self.lang_combo.pack(fill="x", pady=(5, 20))

        # Save Button
        save_btn = tk.Button(
            main_frame, text=messenger("gui_save_btn"), command=self.save, bg="#e1e1e1", padx=10, pady=5
        )
        save_btn.pack(fill="x", pady=(10, 0))

        help_label = tk.Label(
            main_frame, text=messenger("gui_create_api"), fg="blue", cursor="hand2", font=("Segoe UI", 8)
        )
        help_label.pack(pady=(15, 0))

        view_apis_label = tk.Label(
            main_frame, text=messenger("gui_view_apis"), fg="blue", cursor="hand2", font=("Segoe UI", 8)
        )
        view_apis_label.pack(pady=(5, 0))

        help_label.bind("<Button-1>", lambda e: open_url("https://www.last.fm/api/account/create"))
        view_apis_label.bind("<Button-1>", lambda e: open_url("https://www.last.fm/api/accounts"))

    def create_input(self, parent, label_text, current_val, is_secret=False):
        tk.Label(parent, text=label_text).pack(anchor="w", pady=(5, 0))

        clean_val = current_val if not current_val.startswith("<") else ""
        entry = tk.Entry(parent, show="*" if is_secret else "")
        entry.insert(0, clean_val)
        entry.pack(fill="x", pady=(2, 5))
        return entry

    def save(self):
        config_data = {
            "API": {"KEY": self.entry_api_key.get().strip(), "SECRET": self.entry_api_secret.get().strip()},
            "APP": {"LANG": self.lang_var.get()},
            "USER": {"USERNAME": self.entry_username.get().strip()},
        }

        if not all([config_data["API"]["KEY"], config_data["API"]["SECRET"], config_data["USER"]["USERNAME"]]):
            show_warning(messenger("gui_warning_title"), messenger("gui_warning_body"), parent=self.root)
            return

        if self.on_save(config_data):
            self.root.quit()
            self.root.destroy()

    def run(self):
        self.root.mainloop()
