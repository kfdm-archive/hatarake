# -*- coding: utf-8 -*-
import datetime
import logging
import os

import pytz
import rumps
import hatarake.shim
import hatarake.report
import hatarake.models
import hatarake.config

from gntp.config import GrowlNotifier

POMODORO_DB = os.path.join(
    os.path.expanduser("~"),
    'Library',
    'Application Support',
    'Pomodoro',
    'Pomodoro.sql'
)

CONFIG_PATH = os.path.join(
    os.path.expanduser("~"),
    'Library',
    'Application Support',
    'Hatarake',
    'config.ini'
)

GROWL_INTERVAL = 30


class Hatarake(hatarake.shim.Shim):
    def __init__(self):
        super(Hatarake, self).__init__("Hatarake")
        self.menu = ["Reload", "Debug", "Report"]
        self.label = self.menu["Reload"]
        self.delay = GROWL_INTERVAL

        self.reload(None)

        self.notifier = GrowlNotifier(
            applicationName='Hatarake',
            notifications=['Nag'],
        )
        self.notifier.register()

    def alert(self, fmt, *args, **kwargs):
        self.notifier.notify(
            noteType='Nag',
            title=u"働け".encode('utf8', 'replace'),
            description=fmt.format(*args).encode('utf8', 'replace'),
            sticky=True,
            identifier=__file__,
        )

    @rumps.timer(1)
    def refresh(self, sender):
        now = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        delta = now - self.when

        if delta.total_seconds() % self.delay == 0:
            self.alert(u'[{0}] was {1} ago', self.zname, delta)

        self.label.title = u'Last pomodoro [{0}] was {1} ago'.format(self.zname, delta)

        # If delta is more than a day ago, show the infinity symbol to avoid
        # having a super long label in our menubar
        if delta.days:
            delta = u'∞'
        self.title = u'働 {0}'.format(delta)

    @rumps.clicked("Reload")
    def reload(self, sender):
        self.model = hatarake.models.Pomodoro(POMODORO_DB)
        self.config = hatarake.config.Config(CONFIG_PATH)
        self.zname, self.when = self.model.most_recent()

    @rumps.clicked("Debug")
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

    @rumps.clicked("Report")
    def renderreport(self, sender):
        hatarake.report.render_report(self.model, self.config)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    Hatarake().run()
