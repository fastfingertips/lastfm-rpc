from loguru import logger
from packaging import version

import constants.project as project
from utils.http import fetch


def check_for_updates():
    """
    Checks GitHub for the latest release and compares it with the current VERSION.
    Returns a tuple (is_available, latest_version_name, html_url)
    """
    try:
        response = fetch(project.GITHUB_RELEASES_URL, timeout=5)
        if response.status != 200:
            return False, None, None

        data = response.json()
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        return False, None, None

    if data:
        latest_version = data.get("tag_name", "").replace("v", "")
        current_version = project.VERSION.replace("v", "")

        try:
            if version.parse(latest_version) > version.parse(current_version):
                logger.info(f"New update available: {latest_version} (Current: {project.VERSION})")
                return True, data.get("tag_name"), data.get("html_url")
            logger.info(f"App is up to date: {project.VERSION}")
        except Exception as e:
            logger.error(f"Error parsing version: {e}")

    return False, None, None
