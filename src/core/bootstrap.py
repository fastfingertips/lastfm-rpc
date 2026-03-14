import sys

from loguru import logger

from core.config import config
from core.ui.gui import ConfigGUI

logger = logger.bind(name="bootstrap")


def ensure_config_ready() -> bool:
    """
    Checks if the application configuration is complete.
    If not, opens the settings GUI for the user to fill in.
    Returns True if config is ready, False if user should be prompted to restart or app exited.
    """
    if config.is_complete():
        return True

    logger.warning("Configuration incomplete. launching Setup Wizard...")

    def on_initial_save(new_data):
        # Flatten and save
        success = config.save(
            new_data.get("USER", {}).get("USERNAME"),
            new_data.get("API", {}).get("KEY"),
            new_data.get("API", {}).get("SECRET"),
            new_data.get("APP", {}).get("LANG"),
        )
        if success:
            logger.info("Initial configuration saved successfully.")
            # We exit after initial save to ensure a clean start with the new config
            # as many services initialize based on config values.
            return True
        return False

    # Block until GUI is closed
    ConfigGUI.launch(config, on_initial_save, is_wizard=True)

    # After GUI closes, check again. If still incomplete (cancelled), exit.
    if not config.is_complete():
        logger.error("Setup was cancelled or incomplete. Exiting.")
        sys.exit(0)

    return True
