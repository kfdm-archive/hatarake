'''
Wrappers around Python requests

This allows us to handle all the custom headers in a single place
'''
from __future__ import absolute_import

import requests
from functools import wraps

from hatarake.version import __version__

USER_AGENT = 'Hatarake/%s https://github.com/kfdm/hatarake' % __version__

def add_args(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['user-agent'] = USER_AGENT
        return func(*args, **kwargs)
    return wrapper

get = add_args(requests.get)
post = add_args(requests.post)
