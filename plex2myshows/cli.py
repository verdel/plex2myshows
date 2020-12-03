#!/usr/bin/env python

import click
import sys
import pickle
import logging
import logging.handlers
from plexapi.server import PlexServer
from plex2myshows.modules.plex import Plex
from plex2myshows.modules.myshows import MyShows

log = logging.getLogger('plex2myshows')
log.setLevel(logging.INFO)
if sys.platform == "linux" or sys.platform == "linux2":
    handler = logging.handlers.SysLogHandler('/dev/log')
elif sys.platform == "darwin":
    handler = logging.handlers.SysLogHandler(address='/var/run/syslog')
formatter = logging.Formatter('%(name)s: [%(levelname)s] %(message)s')
handler.formatter = formatter
log.addHandler(handler)


@click.command(help='Sync watched series episodes from Plex Media Server to MyShows.me')
@click.option('--plex-url',
              metavar='<url>',
              required=True,
              help='Plex Media Server URL')
@click.option('--plex-token',
              metavar='<token>',
              required=True,
              help='Plex Media Server access token')
@click.option('--plex-section',
              metavar='<section>',
              required=True,
              help='Plex Media Server section to sync')
@click.option('--myshows-api-url',
              metavar='<url>',
              required=True,
              help='MyShows.Me APIv2 URL')
@click.option('--myshows-username',
              metavar='<username>',
              required=True,
              help='MyShows.Me username')
@click.option('--myshows-password',
              metavar='<password>',
              required=True,
              help='MyShows.Me password')
@click.option('--cache-dir',
              required=False,
              default='/tmp',
              help='Plex2Myshows cache directory path')
@click.option('--what-if',
              default=False,
              metavar='<boolean>',
              is_flag=True,
              help='No sync only show episodes')
def cli(plex_url, plex_token, plex_section, myshows_api_url, myshows_username, myshows_password, cache_dir, what_if):
    try:
        myshows = MyShows(myshows_api_url, myshows_username, myshows_password)
    except Exception as exc:
        print(exc)
        log.error(exc)
        sys.exit(1)

    try:
        plex_instance = PlexServer(plex_url, plex_token)
    except Exception as exc:
        print('No Plex Media Server found at {}'.format(plex_url))
        log.error(exc)
        sys.exit(1)

    plex = Plex(plex_instance)
    try:
        watched_episodes = plex.get_watched_episodes(plex_section)
        myshows_series_id = {}

        try:
            with open('{}/series_cache'.format(cache_dir), 'rb') as cache_file:
                series_cache = pickle.load(cache_file)
        except EOFError:
            series_cache = []
        series_cache_size = len(series_cache)
        for entry in watched_episodes:
            if entry.ratingKey in series_cache:
                continue
            entry_key = (entry.grandparentTitle, plex_instance.fetchItem(
                entry.grandparentRatingKey).year)
            if entry_key not in myshows_series_id:
                series_id = myshows.get_series_id(
                    entry.grandparentTitle, plex_instance.fetchItem(entry.grandparentRatingKey).year)
                myshows_series_id.update({entry_key: series_id})
            else:
                series_id = myshows_series_id[entry_key]

            if series_id:
                episode_id = myshows.get_episode_id(
                    series_id, entry.parentIndex, entry.index)
                if episode_id:
                    myshows_watched_episodes = myshows.get_watched_episodes_id(
                        series_id)
                    if not myshows_watched_episodes or episode_id not in myshows_watched_episodes:
                        info = myshows.get_episode_info(episode_id)
                        if what_if:
                            if info:
                                print('{} season {} episode {} will be marked as watched'.format(info['series_title'],
                                                                                                 info['season'],
                                                                                                 info['episode']))
                                log.info('{} season {} episode {} will be marked as watched'.format(info['series_title'],
                                                                                                    info['season'],
                                                                                                    info['episode']))
                            else:
                                print(
                                    'Episode with id {} not found'.format(episode_id))
                                log.warning(
                                    'Episode with id {} not found'.format(episode_id))
                        else:
                            if myshows.mark_episode_as_watch(episode_id):
                                print('{} season {} episode {} mark as watched'.format(info['series_title'],
                                                                                       info['season'],
                                                                                       info['episode']))
                                log.info('{} season {} episode {} mark as watched'.format(info['series_title'],
                                                                                          info['season'],
                                                                                          info['episode']))
                                series_cache.append(entry.ratingKey)
                    else:
                        series_cache.append(entry.ratingKey)
                else:
                    print('{} season {} episode {} not found'.format(entry.grandparentTitle,
                                                                     entry.parentIndex,
                                                                     entry.index))
                    log.warning('{} season {} episode {} not found'.format(entry.grandparentTitle,
                                                                           entry.parentIndex,
                                                                           entry.index))

            else:
                print('Series {} not found'.format(entry.grandparentTitle))
                log.warning('Series {} not found'.format(
                    entry.grandparentTitle))
        if len(series_cache) != series_cache_size:
            with open('{}/series_cache'.format(cache_dir), 'wb+') as cache_file:
                pickle.dump(series_cache, cache_file)

    except Exception as exc:
        print(exc)
        log.error(exc)
        sys.exit(1)


if __name__ == '__main__':
    cli()
