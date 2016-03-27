# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
import logging
import platform
import webbrowser

import dateutil
import gntp.config
import pytz
import hatarake.net as requests
import rumps
from icalendar import Calendar

import hatarake
import hatarake.config
import hatarake.shim

LOGGER = logging.getLogger(__name__)

MENU_RELOAD = u'Reload'
MENU_DEBUG = u'💻Debug'
MENU_ISSUE = u'⚠️Issues'
MENU_REMAINING = u'Remaining'

PRIORITY_VERY_HIGH = datetime.timedelta(minutes=30)
PRIORITY_HIGH = datetime.timedelta(minutes=15)
PRIORITY_LOW = datetime.timedelta(minutes=5)

CONFIG = hatarake.config.Config(hatarake.CONFIG_PATH)


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
            notifications=['Nag']
        )
        self.growl.register()

    def nag(self, title, delta, **kwargs):
        if delta < PRIORITY_LOW:
            return  # Skip low priority nags
        if delta > PRIORITY_VERY_HIGH:
            kwargs['priority'] = 2
        elif delta > PRIORITY_HIGH:
            kwargs['priority'] = 1

        self.growl.notify(
            noteType='Nag',
            title=u"働け".encode('utf8', 'replace'),
            description=u'[{0}] was {1} ago'.format(title, delta).encode('utf8', 'replace'),
            sticky=True,
            identifier=__file__,
            **kwargs
        )


class Hatarake(hatarake.shim.Shim):
    def __init__(self):
        super(Hatarake, self).__init__("Hatarake", "Hatarake")

        self.delay = hatarake.GROWL_INTERVAL
        self.notifier = Growler()
        self.last_pomodoro_name = None
        self.last_pomodoro_timestamp = None
        self.disabled_until = self.now()

        self.reload(None)

    def now(self):
        return datetime.datetime.now(dateutil.tz.tzlocal())

    @rumps.timer(1)
    def _update_clock(self, sender):
        now = self.now().replace(microsecond=0)
        tomorrow = now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
        delta = now - self.last_pomodoro_timestamp

        LOGGER.debug('Pomodoro %s %s, %s', self.title, self.last_pomodoro_timestamp, now)

        if now > self.disabled_until:
            if delta.total_seconds() % self.delay == 0:
                self.notifier.nag(self.last_pomodoro_name, delta)

        self.menu[MENU_RELOAD].title = u'⏰Last pomodoro [{0}] was {1} ago'.format(
            self.last_pomodoro_name,
            delta
        )

        # If delta is more than a day ago, show the infinity symbol to avoid
        # having a super long label in our menubar
        if delta.days:
            delta = u'∞'
        self.title = u'⏳{0}'.format(delta)

        self.menu[MENU_REMAINING].title = u'⌛️Time Remaining today: {}'.format(tomorrow - now)

    @rumps.timer(300)
    @rumps.clicked(MENU_RELOAD)
    def reload(self, sender):
        calendar_url = CONFIG.config.get('feed', 'nag')

        try:
            result = requests.get(calendar_url)
        except IOError:
            self.last_pomodoro_name = 'Error loading calendar'
            self.last_pomodoro_timestamp = self.now().replace(microsecond=0)
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

        self.last_pomodoro_name = recent['SUMMARY']
        self.last_pomodoro_timestamp = recent['DTEND'].dt

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

    @rumps.clicked('Pause for 15m')
    def mute_1m(self, sender):
        sender.state = not sender.state
        if sender.state:
            self.disabled_until = self.now() + datetime.timedelta(minutes=15)
            LOGGER.debug('Pausing alerts until %s', self.disabled_until)
        else:
            self.disabled_until = self.now()
            LOGGER.debug('Unpausing alerts')

    @rumps.clicked('Pause for 1h')
    def mute_1h(self, sender):
        sender.state = not sender.state
        if sender.state:
            self.disabled_until = self.now() + datetime.timedelta(hours=1)
            LOGGER.debug('Pausing alerts until %s', self.disabled_until)
        else:
            self.disabled_until = self.now()
            LOGGER.debug('Unpausing alerts')

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    Hatarake().run()
