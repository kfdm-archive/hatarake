import logging
from hatarake.app import Hatarake


def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('gntp').setLevel(logging.INFO)
    Hatarake().run()

if __name__ == "__main__":
    main()
