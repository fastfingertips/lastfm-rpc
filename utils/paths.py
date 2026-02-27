"""Centralized path management for the application."""

import os
import sys


def get_project_root() -> str:
    """
    Returns the absolute path to the project root directory.
    Handles both source execution and frozen (Nuitka/PyInstaller) execution.
    """
    if getattr(sys, "frozen", False):
        # If running as an executable
        return os.path.dirname(sys.executable)

    # When running as a script, we assume this file is in utils/ and the root is one level up
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)


def get_asset_path(filename: str) -> str:
    """Returns the absolute path to an asset file."""
    return os.path.join(get_project_root(), "assets", filename)


def get_translation_path(lang_code: str) -> str:
    """Returns the absolute path to a translation file."""
    return os.path.join(get_project_root(), "translations", f"{lang_code}.yaml")


def get_log_dir() -> str:
    """Returns the absolute path to the logs directory and ensures it exists."""
    path = os.path.join(get_project_root(), "logs")
    if not os.path.exists(path):
        os.makedirs(path)
    return path
