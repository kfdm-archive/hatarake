from setuptools import setup

APP = ['hatarake/cli.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
    },
    'packages': ['rumps', 'gntp', 'jinja2'],
}

setup(
    name='Hatarake',
    author='Paul Traylor',
    version='0.1.0',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=['rumps', 'gntp', 'jinja2'],
)
