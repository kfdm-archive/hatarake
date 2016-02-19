import ConfigParser
import logging
import re
import codecs

logger = logging.getLogger(__name__)


WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
WEEKENDS = ['Saturday', 'Sunday']


class Config():
    def __init__(self, path):
        self.path = path
        logger.debug('Loaded config from %s', self.path)
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(codecs.open(self.path, 'r', 'utf8'))

    def getboolean(self, section, option, default=None):
        try:
            return self.config.getboolean(section, option)
        except ConfigParser.NoSectionError:
            return default
        except ConfigParser.NoOptionError:
            return default

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
                if self.config.has_option('days', 'Weekends'):
                    return self.config.getint('days', 'Weekends')

        return default

    def getlist(self, key):
        for option in self.config.options(key):
            config = self.config.get(key, option)
            for item in config.strip().split('\n'):
                yield option, item.strip()

    def replacements(self):
        replacements = {}
        if self.config.has_section('replacements'):
            for option, expression in self.getlist('replacements'):
                replacements[re.compile(expression, re.X)] = option
        return replacements
