# -*- coding: utf-8 -*-
import datetime
import logging
import webbrowser

import gntp.config
import pytz
import requests
import rumps
from icalendar import Calendar

import hatarake
import hatarake.config
import platform
import hatarake.shim

LOGGER = logging.getLogger(__name__)

MENU_RELOAD = 'Reload'
MENU_DEBUG = 'Debug'
MENU_ISSUE = 'Issues'

PRIORITY_VERY_HIGH = datetime.timedelta(minutes=30)
PRIORITY_HIGH = datetime.timedelta(minutes=15)


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

        self.reload(None)

    @rumps.timer(1)
    def _update_clock(self, sender):
        now = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        delta = now - self.last_pomodoro_timestamp

        LOGGER.debug('Pomodoro %s %s, %s', self.title, self.last_pomodoro_timestamp, now)

        if delta.total_seconds() % self.delay == 0:
            self.notifier.nag(self.last_pomodoro_name, delta)

        self.menu[MENU_RELOAD].title = u'Last pomodoro [{0}] was {1} ago'.format(
            self.last_pomodoro_name,
            delta
        )

        # If delta is more than a day ago, show the infinity symbol to avoid
        # having a super long label in our menubar
        if delta.days:
            delta = u'∞'
        self.title = u'働 {0}'.format(delta)

    @rumps.timer(300)
    @rumps.clicked(MENU_RELOAD)
    def reload(self, sender):
        config = hatarake.config.Config(hatarake.CONFIG_PATH)
        calendar_url = config.config.get('feed', 'nag')

        result = requests.get(calendar_url, headers={'User-Agent': hatarake.USER_AGENT})
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

    @rumps.clicked(MENU_ISSUE)
    def issues(self, sender):
        webbrowser.open(hatarake.ISSUES_LINK)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    Hatarake().run()
