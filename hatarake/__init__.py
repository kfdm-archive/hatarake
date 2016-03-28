import os
import platform
from hatarake.version import __version__

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
else:
    CONFIG_PATH = os.path.join(
        os.path.expanduser("~"),
        '.config',
        'Hatarake',
        'config.ini',
    )
