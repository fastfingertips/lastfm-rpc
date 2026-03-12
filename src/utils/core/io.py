"""File interaction and I/O utilities."""

import os

import yaml
from loguru import logger

logger = logger.bind(name="io")


def load_yaml(filepath: str) -> dict | None:
    """Safely loads a YAML file and returns its contents. Returns None if missing or invalid."""
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load YAML from {filepath}: {e}")
        return None


def save_yaml(filepath: str, data: dict) -> bool:
    """Saves dictionary data to a YAML file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        logger.error(f"Failed to save YAML to {filepath}: {e}")
        return False
