import os
import platform
import logging
from hatarake.version import __version__

logger = logging.getLogger(__name__)

ISSUES_LINK = 'https://github.com/kfdm/hatarake/issues'
ISSUES_API = 'https://api.github.com/repos/kfdm/hatarake/issues?state=open'

USER_AGENT = 'Hatarake/%s https://github.com/kfdm/hatarake' % __version__

GROWL_INTERVAL = 30

if 'Darwin' in platform.uname():
    CONFIG_PATH = os.path.join(
        os.path.expanduser("~"),
        'Library',
        'Application Support',
        'Hatarake',
        'config.ini'
    )
    DB_PATH = os.path.join(
        os.path.expanduser("~"),
        'Library',
        'Application Support',
        'Hatarake',
        'history.db'
    )
else:
    CONFIG_PATH = os.path.join(
        os.path.expanduser("~"),
        '.config',
        'Hatarake',
        'config.ini',
    )
    DB_PATH = os.path.join(
        os.path.expanduser("~"),
        '.config',
        'Hatarake',
        'history.db',
    )

try:
    from raven.conf import setup_logging
    from raven.handlers.logging import SentryHandler
    from hatarake.config import Config

    config = Config(CONFIG_PATH)

    setup_logging(SentryHandler(config.get('raven', 'dsn')))
except ImportError:
    logging.warning('Unable to import raven')
except ValueError:
    logging.warning('Invalid DNS')
else:
    logging.debug('Initialized Raven')
