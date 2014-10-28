import logging
from hatarake.app import POMODORO_DB, CONFIG_PATH
from hatarake.report import render_report
from hatarake.models import Pomodoro
from hatarake.config import Config


def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('gntp').setLevel(logging.INFO)

    model = Pomodoro(POMODORO_DB)
    config = Config(CONFIG_PATH)
    render_report(model, config)


if __name__ == "__main__":
    main()
