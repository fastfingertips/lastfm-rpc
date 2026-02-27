from core.config import config
from utils.logger import setup_logging

# Configure enhanced logging as early as possible
setup_logging(level="INFO")

from loguru import logger


def check_config():
    """Checks if the configuration is complete. If not, opens the GUI."""
    if not config.is_complete():
        logger.warning("Configuration incomplete or placeholder detected. Opening settings...")
        import sys

        from utils.dialogs import ask_config_gui

        def save_and_exit(new_config):
            # Extract values from new_config dict
            u = new_config.get("USER", {}).get("USERNAME", config.username)
            k = new_config.get("API", {}).get("KEY", config.api_key)
            s = new_config.get("API", {}).get("SECRET", config.api_secret)
            lang = new_config.get("APP", {}).get("LANG", config.app_lang)

            if config.save(u, k, s, lang):
                logger.info("Configuration saved successfully. Please restart the application.")
                sys.exit(0)
            return False

        current_vals = config.get_all_config()
        ask_config_gui(current_vals, save_and_exit)
        return False
    return True


def main():
    if check_config():
        from core.application import App

        try:
            app = App()
            app.run()
        except Exception as e:
            logger.critical(f"Application failed to start: {e}")


if __name__ == "__main__":
    main()
