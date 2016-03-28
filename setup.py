from platform import platform
from setuptools import setup
from hatarake import __version__

kwargs = {}
install_requires=[
    'certifi',
    'click',
    'icalendar',
    'requests',
]

if 'Darwin' in platform():
    kwargs['app'] = ['hatarake/app.py']
    kwargs['data_files'] = []
    kwargs['setup_requires'] = ['py2app']
    kwargs['options'] = {'py2app': {
        'argv_emulation': True,
        'plist': {
            'LSUIElement': True,
        },
        'packages': [
            'certifi',
            'gntp',
            'icalendar',
            'rumps',
        ],
    }}
    install_requires += [
        'gntp',
        'rumps',
    ]
else:
    kwargs = {}


setup(
    name='Hatarake',
    author='Paul Traylor',
    version=__version__,
    entry_points={
        'console_scripts': [
            'hatarake = hatarake.cli:main'
        ]
    },
    **kwargs
)
