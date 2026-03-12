import logging
import os
import platform
import sys

from loguru import logger

from utils.core.paths import get_log_dir


class InterceptHandler(logging.Handler):
    """
    Standard logging handler to intercept calls from external libraries
    and route them to Loguru.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def log_system_info():
    """Logs essential system and application info for debugging."""
    from constants.project import APP_NAME, VERSION

    # We use a custom 'system' tag/module name in loguru style
    sys_logger = logger.bind(name="system")
    sys_logger.debug("--- System Information ---")
    sys_logger.debug(f"Application: {APP_NAME} v{VERSION}")
    sys_logger.debug(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    sys_logger.debug(f"Architecture: {platform.machine()}")
    sys_logger.debug(f"Python Version: {sys.version}")
    sys_logger.debug(f"Executable: {sys.executable}")
    sys_logger.debug(f"Working Directory: {os.getcwd()}")
    sys_logger.debug("--------------------------")


def setup_logging(level="INFO"):
    """Configures Loguru for the application."""

    # Remove default loguru handler
    logger.remove()

    # 1. Console Handler (Colored & Vibrant)
    # Using loguru's rich formatting
    # <green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>
    # We'll try to keep it close to our previous style
    console_format = (
        "<white>[{time:HH:mm:ss}]</white> "
        "<level>{level.icon} {level: <8}</level> "
        "<blue>[{extra[name]}]</blue> "
        "- {message}"
    )

    logger.add(sys.stdout, level=level, format=console_format, colorize=True, backtrace=True, diagnose=True)

    # 2. File Handler (with Rotation and Compression)
    log_dir = get_log_dir()

    file_format = "[{time:YYYY-MM-DD HH:mm:ss}] {level: <8} [{extra[name]}] [{file}:{line}] {function}() - {message}"

    logger.add(
        os.path.join(log_dir, "app.log"),
        level="DEBUG",
        format=file_format,
        rotation="5 MB",
        retention="3 days",
        compression="zip",
        encoding="utf-8",
    )

    # 3. Intercept standard logging (for libraries like pylast, pypresence)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Adjust levels for specific libraries to reduce noise
    for lib in ["httpcore", "httpx", "pylast", "pypresence", "urllib3", "pystray", "asyncio"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    # Initialize daily logger binding to avoid KeyError if name is missing
    # We do this by patching the logger to default to 'app' if no name is bound
    logger.configure(extra={"name": "app"})

    # Log system metadata on startup
    log_system_info()

    return logger
