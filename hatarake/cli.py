import logging
import json
import click
import requests

from hatarake.app import CONFIG_PATH, POMODORO_DB
from hatarake.config import Config
from hatarake.models import Pomodoro
from hatarake.report import render_report


@click.group()
def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('gntp').setLevel(logging.INFO)


@main.command()
@click.option('--start', help='start time')
@click.argument('duration', type=int)
@click.argument('title')
def submit(start, duration, title):
    config = Config(CONFIG_PATH)
    api = config.config.get('server', 'api')
    token = config.config.get('server', 'token')

    response = requests.post(
        api,
        headers={'Authorization': 'Token %s' % token},
        data={
            'created': start,
            'duration': duration,
            'title': title,
        }
    )
    print response.text


@main.command()
def report():
    model = Pomodoro(POMODORO_DB)
    config = Config(CONFIG_PATH)
    render_report(model, config)
