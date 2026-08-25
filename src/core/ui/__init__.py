"""Settings UI package.

This package installs a small integration hook that adds the built-in log
viewer button to the settings window when it is displayed.
"""

import tkinter as tk

_LOG_VIEWER_INJECTED_ATTR = "_log_viewer_button_injected"


def _open_log_viewer(root) -> None:
    from utils.gui.log_viewer import show_log_viewer

    try:
        show_log_viewer(parent=root)
    except Exception:
        pass


def _inject_log_viewer_button(root) -> None:
    try:
        if getattr(root, _LOG_VIEWER_INJECTED_ATTR, False):
            return

        from utils.app.i18n import messenger

        if root.title() != messenger("gui_title"):
            return

        import customtkinter as ctk

        button = ctk.CTkButton(
            root,
            text=messenger("gui_view_logs"),
            command=lambda: _open_log_viewer(root),
            height=32,
        )
        button.pack(fill="x", side="bottom", padx=10, pady=(0, 10))
        setattr(root, _LOG_VIEWER_INJECTED_ATTR, True)
    except Exception:
        pass


def _schedule_log_viewer_injection(root) -> None:
    if getattr(root, "_log_viewer_injection_scheduled", False):
        return

    try:
        setattr(root, "_log_viewer_injection_scheduled", True)
        root.after(150, _inject_log_viewer_button, root)
    except Exception:
        pass


def _patch_mainloop() -> None:
    if getattr(tk.Tk, "_log_viewer_mainloop_patched", False):
        return

    original_mainloop = tk.Tk.mainloop

    def mainloop(self, *args, **kwargs):
        _schedule_log_viewer_injection(self)
        return original_mainloop(self, *args, **kwargs)

    try:
        tk.Tk.mainloop = mainloop
        setattr(tk.Tk, "_log_viewer_mainloop_patched", True)
    except Exception:
        pass


_patch_mainloop()
