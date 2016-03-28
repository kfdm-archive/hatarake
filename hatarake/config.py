import codecs
import ConfigParser
import logging

logger = logging.getLogger(__name__)


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

    def get(self, section, option, default=None):
        try:
            return self.config.get(section, option)
        except ConfigParser.NoSectionError:
            return default
        except ConfigParser.NoOptionError:
            return default
