#!/usr/bin/env python

import click
import sys
import pickle
import logging
import logging.handlers
from plexapi.server import PlexServer
from modules.plex import Plex
from modules.myshows import MyShows

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
@click.option('--myshows-oauth2-url',
              metavar='<url>',
              required=True,
              help='MyShows.Me OAuth2. Path "/oauth/authorize" and "/oauth/token" will add to url automatic.')
@click.option('--myshows-client-id',
              required=True,
              help='MyShows.Me OAuth2 client id')
@click.option('--myshows-client-secret',
              required=True,
              help='MyShows.Me OAuth2 client secret')
@click.option('--myshows-auth-code',
              required=False,
              help='MyShows.Me OAuth2 authorization code')
@click.option('--work-dir',
              required=False,
              default='/tmp',
              help='Plex2Myshows store path')
@click.option('--what-if',
              default=False,
              metavar='<boolean>',
              is_flag=True,
              help='No sync only show episodes')
def cli(plex_url, plex_token, plex_section, myshows_api_url, myshows_oauth2_url, myshows_client_id, myshows_client_secret, myshows_auth_code, work_dir, what_if):
    try:
        myshows = MyShows(myshows_api_url, myshows_oauth2_url, myshows_client_id, myshows_client_secret, myshows_auth_code, work_dir)
    except Exception as exc:
        print(exc)
        log.error(exc)
        sys.exit(1)

    try:
        plex_instance = PlexServer(plex_url, plex_token)
    except:
        print('No Plex Media Server found at {}'.format(plex_url))
        log.error(exc)
        sys.exit(1)

    plex = Plex(plex_instance)
    try:
        watched_episodes = plex.get_watched_episodes(plex_section)
        myshows_series_id = {}

        try:
            with open('{}/series_cache'.format(work_dir), 'r') as cache_file:
                series_cache = pickle.load(cache_file)
        except IOError:
            series_cache = []
        series_cache_size = len(series_cache)
        for entry in watched_episodes:
            if entry.ratingKey in series_cache:
                continue
            entry_key = (entry.grandparentTitle, plex_instance.library.getByKey(entry.grandparentRatingKey).year)
            if entry_key not in myshows_series_id:
                series_id = myshows.get_series_id(entry.grandparentTitle, plex_instance.library.getByKey(entry.grandparentRatingKey).year)
                myshows_series_id.update({entry_key: series_id})
            else:
                series_id = myshows_series_id[entry_key]

            if series_id:
                episode_id = myshows.get_episode_id(series_id, entry.parentIndex, entry.index)

                if episode_id:
                    myshows_watched_episodes = myshows.get_watched_episodes_id(series_id)
                    if not myshows_watched_episodes or episode_id not in myshows_watched_episodes:
                        info = myshows.get_episode_info(episode_id)
                        if what_if:
                            if info:
                                print('{} season {} episode {} will mark as watched'.format(info['series_title'],
                                                                                            info['season'],
                                                                                            info['episode']))
                                log.info('{} season {} episode {} will mark as watched'.format(info['series_title'],
                                                                                               info['season'],
                                                                                               info['episode']))
                            else:
                                print('Episode with id {} not found'.format(episode_id))
                                log.warning('Episode with id {} not found'.format(episode_id))
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
                log.warning('Series {} not found'.format(entry.grandparentTitle))
        if len(series_cache) != series_cache_size:
            with open('{}/series_cache'.format(work_dir), 'w+') as cache_file:
                pickle.dump(series_cache, cache_file)

    except Exception as exc:
        print(exc)
        log.error(exc)
        sys.exit(1)


if __name__ == '__main__':
    cli()
