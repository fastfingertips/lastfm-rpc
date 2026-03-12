# ruff: noqa: I001
import os
import sys

# Add 'src' to sys.path to allow absolute imports from within the src directory
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from loguru import logger
from utils.core.logger import setup_logging
from utils.app.runtime import setup_global_exception_handler

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
