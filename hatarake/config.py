import ConfigParser
import logging
logger = logging.getLogger(__name__)


WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
WEEKENDS = ['Saturday', 'Sunday']


class Config():
    def __init__(self, path):
        self.path = path
        logger.debug('Loaded config from %s', self.path)
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(self.path))
        print self.config

    def hours(self, ts, default):
        date = ts.date().isoformat()
        logger.info('Checking hour for %s', date)
        if self.config.has_section(date):
            if self.config.has_option(date, 'hours'):
                return self.config.getint(date, 'hours')

        dayoftheweek = ts.strftime("%A")
        logger.info('Checking hour for %s', dayoftheweek)
        if self.config.has_section('days'):
            if self.config.has_option('days', dayoftheweek):
                return self.config.getint('days', dayoftheweek)
            if dayoftheweek in WEEKDAYS:
                if self.config.has_option('days', 'Weekdays'):
                    return self.config.getint('days', 'Weekdays')
            if dayoftheweek in WEEKENDS:
                if self.config.has_option('days', 'Weekend'):
                    return self.config.getint('days', 'Weekend')

        return default
