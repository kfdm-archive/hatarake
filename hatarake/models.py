import datetime
import os
import sqlite3

import pytz

NSTIMEINTERVAL = 978307200
POMODORO_SQL = 'SELECT cast(ZWHEN as integer), ZNAME FROM ZPOMODOROS ORDER BY ZWHEN DESC LIMIT 1'

POMODORO_DB = os.path.join(
    os.path.expanduser("~"),
    'Library',
    'Application Support',
    'Pomodoro',
    'Pomodoro.sql'
)


class Pomodoro(object):
    def __init__(self, path=POMODORO_DB):
        self.path = path

    def most_recent(self):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute(POMODORO_SQL)
            zwhen, zname = cur.fetchone()

        return zname, datetime.datetime.fromtimestamp(
            zwhen + NSTIMEINTERVAL, pytz.utc
        ).replace(microsecond=0)

    def query(self, sql, params):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute(sql, params)
            for result in cur.fetchall():
                yield result
