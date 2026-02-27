from utils.logging_config import setup_logging
# Configure enhanced logging as early as possible
setup_logging(level="INFO")

from loguru import logger
import constants.project as project

def check_config():
    """Checks if the configuration is complete. If not, opens the GUI."""
    if not project.config_manager.is_complete():
        logger.warning("Configuration incomplete or placeholder detected. Opening settings...")
        from utils.ui_utils import ask_config_gui
        import sys

        def save_and_exit(new_config):
            # Extract values from new_config dict
            u = new_config.get('USER', {}).get('USERNAME', project.USERNAME)
            k = new_config.get('API', {}).get('KEY', project.API_KEY)
            s = new_config.get('API', {}).get('SECRET', project.API_SECRET)
            l = new_config.get('APP', {}).get('LANG', project.APP_LANG)
            
            if project.config_manager.save(u, k, s, l):
                logger.info("Configuration saved successfully. Please restart the application.")
                sys.exit(0)
            return False

        current_vals = project.config_manager.get_all_config()
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
