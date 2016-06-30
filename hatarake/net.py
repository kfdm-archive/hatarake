'''
Wrappers around Python requests

This allows us to handle all the custom headers in a single place
'''
from __future__ import absolute_import

import requests
from functools import wraps

from hatarake import USER_AGENT


def add_args(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            kwargs['headers']['user-agent'] = USER_AGENT
        except KeyError:
            kwargs['headers'] = {'user-agent': USER_AGENT}

        if 'token' in kwargs:
            token = kwargs.pop('token')
            kwargs['headers']['Authorization'] = 'Token %s' % token

        return func(*args, **kwargs)
    return wrapper

get = add_args(requests.get)
post = add_args(requests.post)
put = add_args(requests.put)
