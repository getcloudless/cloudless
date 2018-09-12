"""
Logging configuration for this module.  Import it with:

    from <module_name>.logging import logger

"""
import logging

logging.basicConfig()
logger = logging.getLogger(__name__) # pylint: disable=locally-disabled, invalid-name

def set_level(level):
    """
    Set log level for this module.
    """
    logger.setLevel(level)

set_level(logging.WARN)
