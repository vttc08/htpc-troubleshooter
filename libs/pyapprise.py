import logging
from libs.configuration import *
import apprise

logger = logging.getLogger(__name__)
apprise_logger = logging.getLogger("apprise")
apprise_logger.setLevel(logging.WARNING)
urllib_logger = logging.getLogger("urllib3")
urllib_logger.setLevel(logging.WARNING)

apprise_obj = apprise.Apprise()
apprise_obj.add(apprise_url)


