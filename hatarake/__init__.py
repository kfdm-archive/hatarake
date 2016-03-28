import os
from hatarake.version import __version__

ISSUES_LINK = 'https://github.com/kfdm/hatarake/issues'
ISSUES_API = 'https://api.github.com/repos/kfdm/hatarake/issues?state=open'

USER_AGENT = 'Hatarake/%s https://github.com/kfdm/hatarake' % __version__

GROWL_INTERVAL = 30

CONFIG_PATH = os.path.join(
    os.path.expanduser("~"),
    'Library',
    'Application Support',
    'Hatarake',
    'config.ini'
)
