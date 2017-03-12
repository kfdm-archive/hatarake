# -*- coding: utf-8 -*-
from __future__ import absolute_import

import collections
import datetime
import logging
import platform
import webbrowser

import dateutil
import dateutil.parser
import gntp.config
import rumps
from icalendar import Calendar

import hatarake
import hatarake.config
import hatarake.net as requests
import hatarake.shim

LOGGER = logging.getLogger(__name__)

MENU_RELOAD = u'Reload'
MENU_DEBUG = u'💻Debug'
MENU_ISSUE = u'⚠️Issues'
MENU_REMAINING = u'Remaining'
MENU_PAUSE = u'Pause'

MENU_PAUSE_15M = u'Pause for 15m'
MENU_PAUSE_1H = u'Pause for 1h'

PRIORITY_VERY_HIGH = datetime.timedelta(minutes=30)
PRIORITY_HIGH = datetime.timedelta(minutes=15)
PRIORITY_LOW = datetime.timedelta(minutes=5)

CONFIG = hatarake.config.Config(hatarake.CONFIG_PATH)


Pomodoro = collections.namedtuple('Pomodoro', ['name', 'ts'])


class GrowlNotifier(gntp.config.GrowlNotifier):
    def add_origin_info(self, packet):
        """Add optional Origin headers to message"""
        packet.add_header('Origin-Machine-Name', platform.node())
        packet.add_header('Origin-Software-Name', 'Hatarake')
        packet.add_header('Origin-Software-Version', hatarake.__version__)
        packet.add_header('Origin-Platform-Name', platform.system())
        packet.add_header('Origin-Platform-Version', platform.platform())


class Growler(object):
    def __init__(self):
        self.growl = GrowlNotifier(
            applicationName='Hatarake',
            notifications=['Nag', 'Info']
        )
        try:
            self.growl.register()
        except:
            logging.exception('Error registering with growl server')

    def info(self, title, message, **kwargs):
        try:
            self.growl.notify(
                noteType='Info',
                title=title,
                description=message,
                **kwargs
            )
        except:
            logging.exception('Error sending growl message')

    def nag(self, title, delta, **kwargs):
        if delta < PRIORITY_LOW:
            return  # Skip low priority nags
        if delta > PRIORITY_VERY_HIGH:
            kwargs['priority'] = 2
        elif delta > PRIORITY_HIGH:
            kwargs['priority'] = 1

        try:
            self.growl.notify(
                noteType='Nag',
                title=u"働け".encode('utf8', 'replace'),
                description=u'[{0}] was {1} ago'.format(title, delta).encode('utf8', 'replace'),
                sticky=True,
                identifier=__file__,
                **kwargs
            )
        except:
            logging.exception('Error sending growl message')


class Hatarake(hatarake.shim.Shim):
    def __init__(self):
        super(Hatarake, self).__init__("Hatarake", "Hatarake")

        self.delay = hatarake.GROWL_INTERVAL
        self.notifier = Growler()
        self.pomodoro = None
        self.disabled_until = None

        self.reload(None)

    @rumps.timer(1)
    def _update_clock(self, sender):
        if self.pomodoro is None:
            LOGGER.warning('Timestamp is None')
            return

        self.now = datetime.datetime.now(dateutil.tz.tzlocal()).replace(microsecond=0)
        tomorrow = self.now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)

        # Show a normal delta with an hour glass if we have an active Pomodoro
        if self.pomodoro.ts > self.now:
            delta = self.pomodoro.ts - self.now
            self.title = u'⏳{0}'.format(delta)
        # Show an alarm clock if we do not have an active pomodoro
        else:
            delta = self.now - self.pomodoro.ts
            if delta.days:
                self.title = u'⏳{∞}'
            else:
                self.title = u'⏰{0}'.format(delta)

        LOGGER.debug('Pomodoro %s %s, %s', self.title, self.pomodoro.ts, self.now)

        self.menu[MENU_RELOAD].title = u'⏰Last pomodoro [{0}] was {1} ago'.format(
            self.pomodoro.name,
            delta
        )

        self.menu[MENU_REMAINING].title = u'⌛️Time Remaining today: {}'.format(tomorrow - self.now)

        if self.disabled_until and self.disabled_until > self.now:
            self.disabled_until = None
        if self.disabled_until is None:
            if delta.total_seconds() % self.delay == 0:
                self.notifier.nag(self.pomodoro.name, delta)

    if CONFIG.getboolean('feed', 'nag'):
        @rumps.timer(300)
        @rumps.clicked(MENU_RELOAD)
        def reload(self, sender):

            calendar_url = CONFIG.get('feed', 'nag')

            try:
                result = requests.get(calendar_url)
            except IOError:
                self.pomodoro.name = 'Error loading calendar'
                self.pomodoro.ts = self.now.replace(microsecond=0)
                return

            cal = Calendar.from_ical(result.text)
            recent = None

            for entry in cal.subcomponents:
                if recent is None:
                    recent = entry
                    continue
                if 'DTEND' not in entry:
                    continue
                if entry['DTEND'].dt > recent['DTEND'].dt:
                    recent = entry

            self.pomodoro = Pomodoro(
                recent['SUMMARY'],
                recent['DTEND'].dt
            )
    else:
        @rumps.timer(300)
        @rumps.clicked(MENU_RELOAD)
        def reload(self, sender):
            api = CONFIG.get('server', 'api')
            token = CONFIG.get('server', 'token')

            response = requests.get(api, token=token, params={
                'orderby': 'created',
                'limit': 1,
            })
            response.raise_for_status()
            result = response.json()['results'].pop()
            self.pomodoro = Pomodoro(
                result['title'],
                dateutil.parser.parse(result['end']).replace(microsecond=0)
            )

    if CONFIG.getboolean('hatarake', 'development', False):
        @rumps.clicked(MENU_DEBUG)
        def toggledebug(self, sender):
            sender.state = not sender.state
            if sender.state:
                self.delay = 5
                logging.getLogger().setLevel(logging.INFO)
                logging.info('Setting debugging to INFO and delay to %d', self.delay)
            else:
                logging.info('Setting debugging to WARNING and delay to %d', self.delay)
                logging.getLogger().setLevel(logging.WARNING)
                self.delay = hatarake.GROWL_INTERVAL

    if CONFIG.getboolean('hatarake', 'development', False):
        @rumps.clicked(MENU_ISSUE)
        def issues(self, sender):
            webbrowser.open(hatarake.ISSUES_LINK)

    @rumps.clicked(MENU_REMAINING)
    def remaining(self, sender):
        pass

    @rumps.clicked(MENU_PAUSE, MENU_PAUSE_15M)
    def mute_1m(self, sender):
        sender.state = not sender.state
        if sender.state:
            self.disabled_until = self.now + datetime.timedelta(minutes=15)
            self.notifier.info('Pause', 'Pausing alerts until %s' % self.disabled_until)
            self.menu[MENU_PAUSE][MENU_PAUSE_1H].state = False
        else:
            self.disabled_until = None
            self.notifier.info('Unpaused Alerts')

    @rumps.clicked(MENU_PAUSE, MENU_PAUSE_1H)
    def mute_1h(self, sender):
        sender.state = not sender.state
        if sender.state:
            self.disabled_until = self.now + datetime.timedelta(hours=1)
            self.notifier.info('Pause', 'Pausing alerts until %s' % self.disabled_until)
            self.menu[MENU_PAUSE][MENU_PAUSE_15M].state = False
        else:
            self.disabled_until = None
            self.notifier.info('Unpaused Alerts')

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    Hatarake().run()
