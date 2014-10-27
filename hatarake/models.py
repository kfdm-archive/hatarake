import datetime
import sqlite3

import pytz

NSTIMEINTERVAL = 978307200
POMODORO_SQL = 'SELECT cast(ZWHEN as integer), ZNAME FROM ZPOMODOROS ORDER BY ZWHEN DESC LIMIT 1'


class Pomodoro(object):
    def __init__(self, path):
        self.path = path

    def most_recent(self):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute(POMODORO_SQL)
            zwhen, zname = cur.fetchone()

        return zname, datetime.datetime.fromtimestamp(
            zwhen + NSTIMEINTERVAL, pytz.utc
        ).replace(microsecond=0)
