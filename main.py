import sys
import traceback
from utils.logger import setup_logging

# 1. Start logging immediately (to catch early errors)
setup_logging(level="INFO")
from loguru import logger

# 2. Global crash handler (critical for Nuitka standalone builds)
def _global_exception_handler(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.opt(exception=True).critical(f"FATAL CRASH:\n{tb_str}")

sys.excepthook = _global_exception_handler

# 3. Load configuration after logging is ready
logger.info("Initializing configuration...")
from core.config import config
try:
    config.load()
    logger.info("Configuration loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load config: {e}")

def check_config():
    """Ensure configuration is complete, open settings GUI if not."""
    logger.info("Checking configuration completeness...")
    if not config.is_complete():
        logger.warning("Configuration incomplete. Opening settings GUI...")
        from utils.dialogs import ask_config_gui

        def save_and_exit(new_config):
            u = new_config.get("USER", {}).get("USERNAME", config.username)
            k = new_config.get("API", {}).get("KEY", config.api_key)
            s = new_config.get("API", {}).get("SECRET", config.api_secret)
            lang = new_config.get("APP", {}).get("LANG", config.app_lang)

            if config.save(u, k, s, lang):
                logger.info("Config saved. Please restart app.")
                sys.exit(0)
            return False

        current_vals = config.get_all_config()
        ask_config_gui(current_vals, save_and_exit)
        return False
    return True

def main():
    logger.info("Entering main application flow...")
    if check_config():
        logger.info("Importing App class...")
        from core.application import App
        
        try:
            logger.info("Initializing App core...")
            app = App()
            logger.info("App starting run loop...")
            app.run()
        except Exception as e:
            logger.opt(exception=True).critical(f"Startup error: {e}")

if __name__ == "__main__":
    main()
