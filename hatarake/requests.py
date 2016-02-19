'''
Wrappers around Python requests

This allows us to handle all the custom headers in a single place
'''
from __future__ import absolute_import

import requests

from hatarake.version import __version__

USER_AGENT = 'Hatarake/%s https://github.com/kfdm/hatarake' % __version__


def get(*args, **kwargs):
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    kwargs['headers']['user-agent'] = USER_AGENT
    return requests.get(*args, **kwargs)
