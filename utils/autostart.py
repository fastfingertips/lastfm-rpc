import os
import sys
import winreg

from loguru import logger

import constants.project as project

logger = logger.bind(name="autostart")


def toggle_autostart(enabled: bool) -> bool:
    """Toggles Windows auto-start registry key for the application."""
    app_name = project.APP_NAME

    if getattr(sys, "frozen", False):
        # Running as bundled executable (Nuitka)
        app_path = f'"{sys.executable}"'
    else:
        # Running as script
        app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            logger.info(f"Auto-start registered: {app_path}")
        else:
            try:
                winreg.DeleteValue(key, app_name)
                logger.info("Auto-start unregistered.")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logger.error(f"Failed to toggle auto-start: {e}")
        return False
