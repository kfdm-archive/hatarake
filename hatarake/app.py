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
MENU_TOMORROW = u'Remaining'
MENU_PAUSE = u'Pause'

MENU_PAUSE_15M = u'Pause for 15m'
MENU_PAUSE_1H = u'Pause for 1h'

LABEL_ACTIVE = u'⏳{0}'
LABEL_REMAINING = u'⏳{0} remaining for {1}'
LABEL_SINCE = u'⏰Last pomodoro [{0}] was {1} ago'
LABEL_OVERDUE = u'⏰{0}'
LABEL_TOMORROW = u'⌛️Time Remaining today: {}'

PRIORITY_VERY_HIGH = datetime.timedelta(minutes=30)
PRIORITY_HIGH = datetime.timedelta(minutes=15)
PRIORITY_LOW = datetime.timedelta(minutes=5)

GROWL_INTERVAL = 60

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

    def nag(self, title, delta, delay, **kwargs):
        if delta.total_seconds() % delay != 0:
            return

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

        self.delay = GROWL_INTERVAL
        self.notifier = Growler()
        self.pomodoro = None
        self.disabled_until = None
        self.active = False

        self.reload(None)

    def label(self, menu, fmt, *args, **kwargs):
        self.menu[menu].title = fmt.format(*args, **kwargs)

    @rumps.timer(1)
    def _update_clock(self, sender):
        self.now = datetime.datetime.now(dateutil.tz.tzlocal())\
            .replace(microsecond=0)

        if self.pomodoro is None:
            LOGGER.debug('No pomodoro found')
            return
        LOGGER.debug(
            'Pomodoro %s > %s > %s',
            self.pomodoro.name, self.pomodoro.ts, self.now
        )

        self.active = self.pomodoro.ts > self.now

        # Update our menu showing how much time is left today
        remainder = self.now.replace(hour=0, minute=0, second=0) \
            + datetime.timedelta(days=1) - self.now
        self.label(MENU_TOMORROW, LABEL_TOMORROW, remainder)

        # If we have an active Pomodoro, then we can just update our title
        # and be finished
        if self.active:
            delta = self.pomodoro.ts - self.now
            self.title = LABEL_ACTIVE.format(delta)
            self.label(
                MENU_RELOAD, LABEL_REMAINING,
                delta, self.pomodoro.name
                )
            return

        # Show an alarm clock if we do not have an active pomodoro
        delta = self.now - self.pomodoro.ts
        if delta.days:
            self.title = LABEL_OVERDUE.format(u'∞')
        else:
            self.title = LABEL_OVERDUE.format(delta)

        self.label(
            MENU_RELOAD, LABEL_SINCE,
            self.pomodoro.name, delta
            )

        if self.disabled_until:
            if self.disabled_until < self.now:
                return
            self.disabled_until = None

        if self.pomodoro.ts < self.now:
            self.notifier.nag(self.pomodoro.name, delta, self.delay)

    if CONFIG.getboolean('feed', 'nag'):
        @rumps.timer(300)
        @rumps.clicked(MENU_RELOAD)
        def reload(self, sender):

            calendar_url = CONFIG.get('feed', 'nag')

            try:
                result = requests.get(calendar_url)
            except IOError:
                self.pomodoro = Pomodoro(
                    'Error loading calendar',
                    self.now.replace(microsecond=0)
                    )
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
                self.delay = GROWL_INTERVAL

    if CONFIG.getboolean('hatarake', 'development', False):
        @rumps.clicked(MENU_ISSUE)
        def issues(self, sender):
            webbrowser.open(hatarake.ISSUES_LINK)

    @rumps.clicked(MENU_TOMORROW)
    def _tomorrow(self, sender):
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
