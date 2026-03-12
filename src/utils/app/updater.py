from loguru import logger
from packaging import version

import constants.project as project
from utils.net.http import fetch


def check_for_updates():
    """
    Checks GitHub for the latest release and compares it with the current VERSION.
    Returns a tuple (is_available, latest_version_name, html_url)
    """
    data = None
    try:
        response = fetch(project.GITHUB_RELEASES_URL, timeout=5)
        if response and response.status == 200:
            data = response.json()
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        return False, None, None

    if data and isinstance(data, dict):
        latest_tag = data.get("tag_name", "")
        latest_version = latest_tag.replace("v", "")
        current_version = project.VERSION.replace("v", "")

        try:
            if version.parse(latest_version) > version.parse(current_version):
                logger.info(f"New update available: {latest_version} (Current: {project.VERSION})")
                return True, latest_tag, data.get("html_url")
            logger.info(f"App is up to date: {project.VERSION}")
        except Exception as e:
            logger.error(f"Error parsing version: {e}")

    return False, None, None
