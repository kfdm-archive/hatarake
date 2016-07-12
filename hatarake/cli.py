import datetime
import logging
import textwrap
import time

import click

import hatarake
import hatarake.net as requests
from hatarake.config import Config

logger = logging.getLogger(__name__)


@click.group()
@click.option('-v', '--verbosity', count=True)
def main(verbosity):
    logging.basicConfig(level=logging.WARNING - verbosity * 10)
    logging.getLogger('gntp').setLevel(logging.ERROR - verbosity * 10)


@main.command()
@click.option('--start', help='start time')
@click.argument('duration', type=int)
@click.argument('title')
def submit(start, duration, title):
    '''Submit a pomodoro to the server'''
    config = Config(hatarake.CONFIG_PATH)
    api = config.get('server', 'api')
    token = config.get('server', 'token')

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
    response.raise_for_status()
    print response.text


@main.command()
@click.option('--duration', type=int, default=2)
@click.option('--api_server', envvar='HATARAKE_API_SERVER')
@click.option('--api_token', envvar='HATARAKE_API_TOKEN')
@click.argument('title')
def append(duration, title, api_server=None, api_token=None):
    '''Append time to a pomodoro'''
    config = Config(hatarake.CONFIG_PATH)
    api = api_server if api_server else config.get('server', 'api')
    token = api_token if api_token else config.get('server', 'token')

    # Split the tags out of the title
    # For now, we remove the tags from the final title to make things neater
    # but in the future, may want to leave the hash tag in the full title
    tags = {tag.strip("#") for tag in title.split() if tag.startswith("#")}
    title = ' '.join({tag for tag in title.split() if not tag.startswith('#')})

    response = requests.post(
        api + '/append',
        headers={
            'Authorization': 'Token %s' % token,
        },
        data={
            'category': tags,
            'duration': duration,
            'title': title,
        }
    )
    response.raise_for_status()
    print response.text

@main.command()
@click.option('--api_server', envvar='HATARAKE_API_SERVER')
@click.option('--api_token', envvar='HATARAKE_API_TOKEN')
@click.argument('label')
@click.argument('duration', type=int)
def countdown(api_server, api_token, label, duration):
    '''Submit a new countdown'''
    config = Config(hatarake.CONFIG_PATH)
    api = api_server if api_server else config.get('countdown', 'api')
    token = api_token if api_token else config.get('countdown', 'token')

    created = datetime.datetime.now() + datetime.timedelta(minutes=duration)

    response = requests.put(
        api,
        headers={
            'Authorization': 'Token %s' % token,
        },
        data={
            'created': created.replace(microsecond=0).isoformat(),
            'label': label,
        }
    )
    response.raise_for_status()
    print response.text


@main.command()
@click.argument('key')
@click.argument('value')
def stat(key, value):
    '''Submit stat data to server'''
    config = Config(hatarake.CONFIG_PATH)

    response = requests.post(
        config.get('stat', 'api'),
        headers={
            'Authorization': 'Token %s' % config.get('stat', 'token'),
        },
        data={
            'key': key,
            'value': value,
        }
    )
    logger.info('POSTing to %s %s', response.request.url, response.request.body)
    response.raise_for_status()
    print response.text


@main.command()
@click.argument('name', default='heartbeat')
def heartbeat(name):
    config = Config(hatarake.CONFIG_PATH)
    url = config.get('prometheus', 'pushgateway')

    payload = textwrap.dedent('''
    # TYPE {name} gauge
    # HELP {name} Last heartbeat based on unixtimestamp
    {name} {time}
    ''').format(name=name, time=int(time.time())).lstrip()

    response = requests.post(url, data=payload)
    response.raise_for_status()
    click.echo(response)
