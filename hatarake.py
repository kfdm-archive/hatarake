# -*- coding: utf-8 -*-
import datetime
import logging
import os
import sqlite3

import pytz
import rumps

from gntp.config import GrowlNotifier

logging.basicConfig(level=logging.ERROR)

NSTIMEINTERVAL = 978307200

POMODORO_DB = os.path.join(
    os.path.expanduser("~"),
    'Library',
    'Application Support',
    'Pomodoro',
    'Pomodoro.sql'
)

POMODORO_SQL = 'SELECT cast(ZWHEN as integer), ZNAME FROM ZPOMODOROS ORDER BY ZWHEN DESC LIMIT 1'

GROWL_INTERVAL = 30


class Hatarake(rumps.App):
    def __init__(self):
        super(Hatarake, self).__init__("Hatarake")
        self.menu = ["Duration"]
        self.label = self.menu["Duration"]

        with sqlite3.connect(POMODORO_DB) as con:
            cur = con.cursor()
            cur.execute(POMODORO_SQL)
            zwhen, zname = cur.fetchone()

        self.zname = zname
        self.when = datetime.datetime.fromtimestamp(
            zwhen + NSTIMEINTERVAL, pytz.utc
        ).replace(microsecond=0)

        self.notifier = GrowlNotifier(
            applicationName='Hatarake',
            notifications=['Nag'],
        )
        self.notifier.register()

    def alert(self, fmt, *args):
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
        self.label.title = u'Last pomodoro [{0}] was {1} ago'.format(self.zname, delta)
        self.title = u'働け {0}'.format(delta)

        if delta.total_seconds() % GROWL_INTERVAL == 0:
            self.alert(u'[{0}] was {1} ago', self.zname, delta)

if __name__ == "__main__":
    Hatarake().run()
