import logging
from hatarake.cli import Hatarake

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    Hatarake().run()
