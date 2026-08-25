"""Built-in viewer for the application log file."""

import os
import subprocess
import sys
import tkinter as tk

import customtkinter as ctk
from loguru import logger

from utils.app.i18n import messenger
from utils.gui.dialogs import show_warning

logger = logger.bind(name="log_viewer")

LOG_FILE_CANDIDATES = (
    "gpp.log",
    "Gpp.log",
    "lastfm-rpc.log",
    "lastfm_rpc.log",
    "lastfm.log",
    "rpc.log",
    "app.log",
)


def _open_path(path: str) -> None:
    try:
        if sys.platform == "win32":
            start_file = getattr(os, "startfile", None)
            if start_file:
                start_file(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        logger.error(f"Failed to open log file: {e}")


def _candidate_dirs() -> list[str]:
    dirs: list[str] = []

    def add_dir(path: str | None) -> None:
        if path and os.path.isdir(path):
            dirs.append(os.path.abspath(path))

    try:
        from utils.core.paths import get_config_path

        add_dir(os.path.dirname(get_config_path()))
    except Exception:
        pass

    try:
        from utils.core.paths import get_log_path

        add_dir(os.path.dirname(get_log_path()))
    except Exception:
        pass

    if getattr(sys, "frozen", False):
        add_dir(os.path.dirname(sys.executable))
    else:
        add_dir(os.getcwd())
        if sys.argv and sys.argv[0]:
            add_dir(os.path.dirname(os.path.abspath(sys.argv[0])))

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            add_dir(os.path.join(appdata, "lastfm-rpc"))
    elif sys.platform == "darwin":
        add_dir(os.path.join(os.path.expanduser("~"), "Library", "Logs", "lastfm-rpc"))
    else:
        add_dir(os.path.join(os.path.expanduser("~"), ".lastfm-rpc"))

    unique: list[str] = []
    for d in dirs:
        if d not in unique:
            unique.append(d)
    return unique


def _find_log_file() -> str | None:
    try:
        from utils.core.paths import get_log_path

        log_path = get_log_path()
        if log_path and os.path.isfile(log_path):
            return log_path
    except Exception:
        pass

    dirs = _candidate_dirs()

    for d in dirs:
        for name in LOG_FILE_CANDIDATES:
            path = os.path.join(d, name)
            if os.path.isfile(path):
                return path

    fallback: list[tuple[float, str]] = []
    for d in dirs:
        try:
            entries = os.listdir(d)
        except Exception:
            continue

        for name in entries:
            if name.lower().endswith(".log"):
                path = os.path.join(d, name)
                if os.path.isfile(path):
                    try:
                        fallback.append((os.path.getmtime(path), path))
                    except Exception:
                        continue

    if fallback:
        fallback.sort(reverse=True)
        return fallback[0][1]
    return None


def show_log_viewer(parent=None) -> None:
    log_path = _find_log_file()

    if not log_path or not os.path.isfile(log_path):
        show_warning(messenger("gui_log_viewer_title"), messenger("gui_log_file_missing"), parent=parent)
        return

    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read log file {log_path}: {e}")
        show_warning(messenger("gui_log_viewer_title"), f"{messenger('gui_log_file_missing')} ({e})", parent=parent)
        return

    root = ctk.CTkToplevel(parent) if parent is not None else ctk.CTk()
    root.title(messenger("gui_log_viewer_title"))
    root.geometry("900x650")

    if parent is not None:
        try:
            root.transient(parent)
            root.grab_set()
            root.lift()
            root.focus_force()
        except Exception:
            pass

    frame = ctk.CTkFrame(root, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

    text = tk.Text(frame, wrap="none", state="disabled", font=("Consolas", 10), bg="#1e1e1e", fg="#dcdcdc")
    scroll = tk.Scrollbar(frame, command=text.yview)
    text.configure(yscrollcommand=scroll.set)

    text.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    text.configure(state="normal")
    text.insert(tk.END, content)
    text.configure(state="disabled")
    text.see(tk.END)

    bottom = ctk.CTkFrame(root, fg_color="transparent")
    bottom.pack(fill="x", padx=10, pady=(0, 10))
    open_button = ctk.CTkButton(
        bottom,
        text=messenger("gui_open_log_file"),
        command=lambda: _open_path(log_path),
        width=160,
    )
    open_button.pack(side="left", padx=(0, 8))
    close_button = ctk.CTkButton(bottom, text=messenger("exit"), command=root.destroy, width=80)
    close_button.pack(side="right")

    if parent is None:
        root.mainloop()
