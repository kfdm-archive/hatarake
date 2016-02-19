import logging

import click
import hatarake.requests as requests

from hatarake.config import Config
from hatarake.models import Pomodoro
from hatarake.report import render_report
import hatarake


@click.group()
def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('gntp').setLevel(logging.INFO)


@main.command()
@click.option('--start', help='start time')
@click.argument('duration', type=int)
@click.argument('title')
def submit(start, duration, title):
    config = Config(hatarake.CONFIG_PATH)
    api = config.config.get('server', 'api')
    token = config.config.get('server', 'token')

    response = requests.post(
        api,
        headers={
            'Authorization': 'Token %s' % token,
        },
        data={
            'created': start,
            'duration': duration,
            'title': title,
        }
    )
    print response.text


@main.command()
@click.option('--duration', type=int, default=2)
@click.option('--api_server', envvar='HATARAKE_API_SERVER')
@click.option('--api_token', envvar='HATARAKE_API_TOKEN')
@click.argument('title')
def append(duration, title, api_server=None, api_token=None):
    config = Config(hatarake.CONFIG_PATH)
    api = api_server if api_server else config.config.get('server', 'api')
    token = api_token if api_token else config.config.get('server', 'token')

    # Split the tags out of the title
    # For now, we remove the tags from the final title to make things neater
    # but in the future, may want to leave the hash tag in the full title
    tags = {tag.strip("#") for tag in title.split() if tag.startswith("#")}
    title = ' '.join({tag for tag in title.split() if not tag.startswith('#')})

    response = requests.post(
        api + 'append/',
        headers={
            'Authorization': 'Token %s' % token,
        },
        data={
            'category': tags,
            'duration': duration,
            'title': title,
        }
    )
    print response.text

@main.command()
def report():
    model = Pomodoro()
    config = Config(hatarake.CONFIG_PATH)
    timezone = config.config.get('report', 'timezone', 'UTC')
    render_report(model, config, timezone)
