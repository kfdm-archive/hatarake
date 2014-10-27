import logging
from hatarake.app import Hatarake

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('gntp').setLevel(logging.INFO)
    Hatarake().run()
