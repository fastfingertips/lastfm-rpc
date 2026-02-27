from loguru import logger
from packaging import version
import constants.project as project
from utils.request_utils import get_json

def check_for_updates():
    """
    Checks GitHub for the latest release and compares it with the current VERSION.
    Returns a tuple (is_available, latest_version_name, html_url)
    """
    data = get_json(project.GITHUB_RELEASES_URL, timeout=5)
    
    if data:
        latest_version = data.get('tag_name', '').replace('v', '')
        current_version = project.VERSION.replace('v', '')
        
        try:
            if version.parse(latest_version) > version.parse(current_version):
                logger.info(f"New update available: {latest_version} (Current: {project.VERSION})")
                return True, data.get('tag_name'), data.get('html_url')
            else:
                logger.info(f"App is up to date: {project.VERSION}")
        except Exception as e:
            logger.error(f"Error parsing version: {e}")
            
    return False, None, None
