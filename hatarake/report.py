import logging
import collections
import datetime
import pytz
import time
from hatarake.models import NSTIMEINTERVAL

REPORT_FORMAT = u'{hours:0>2}:{minutes:0>2} {percent:>6.2%} {pomodoro}'
REPORT_SQL = 'SELECT Z_PK, cast(ZWHEN as integer), ZDURATIONMINUTES, ZNAME FROM ZPOMODOROS WHERE ZWHEN > ? AND ZWHEN < ? ORDER BY ZWHEN DESC'
TIME_ZONE = 'America/Los_Angeles'


logger = logging.getLogger(__name__)

class PomodoroBucket(object):
    @classmethod
    def midnight(cls, datetime):
        return time.mktime(
            datetime.replace(
                hour=0, minute=0, second=0, microsecond=0
            ).timetuple()
        ) - NSTIMEINTERVAL

    @classmethod
    def get(cls, database, start, minutes, config):
        # Assuming start is midnight, add a day to get the end
        end = start + 24 * 60 * 60
        buckets = collections.defaultdict(int)
        replacements = config.replacements()
        logging.debug('Using %s replacements', replacements)
        buckets['Unknown'] = minutes

        for zpk, zwhen, zminutes, zname in database.query(REPORT_SQL, (start, end)):
            for regex, replace in replacements.items():
                if regex.match(zname):
                    logger.debug('Replaced %s with %s', zname, replace)
                    zname = replace
            buckets[zname] += zminutes
            buckets['Unknown'] -= zminutes
        return sorted(buckets.items(), key=lambda x: x[1], reverse=True)


def render_report(model, config):
    # Get midnight today (in the current timezone) as our query point
    ts = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    hours = config.hours(ts, 9)
    logger.debug('Using %s hours for report', hours)

    start = PomodoroBucket.midnight(ts)

    minutes = hours * 60

    buckets = PomodoroBucket.get(model, start, minutes, config)

    print 'Breakdown for {0} hours'.format(hours)
    print '-' * 80
    for key, value in buckets:
        print REPORT_FORMAT.format(
            pomodoro=key,
            hours=value / 60,
            minutes=value % 60,
            percent=float(value) / float(minutes),
        )
