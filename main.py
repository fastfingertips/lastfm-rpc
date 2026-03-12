# ruff: noqa: I001
import sys
from loguru import logger
from utils.logger import setup_logging
from utils.runtime import setup_global_exception_handler

# 1. Early Initialization (Logging & Safety)
setup_logging(level="INFO")
setup_global_exception_handler()

# 2. Bootstrap (Config & Environment)
from core.config import config
from core.bootstrap import ensure_config_ready


def main():
    """Main entry point of the application."""
    logger.info("Application starting...")

    # Load config and ensure it's ready for use
    config.load()
    if not ensure_config_ready():
        return

    # Start the application orchestrator
    from core.application import App

    try:
        app = App()
        app.run()
    except Exception as e:
        logger.opt(exception=True).critical(f"Unhandled startup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
