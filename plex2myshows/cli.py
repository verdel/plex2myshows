#!/usr/bin/env python
import click
import sys
from plexapi.server import PlexServer
from modules.plex import Plex
from modules.myshows import MyShows
from modules.graylog import Graylog


@click.command(help='Sync watched series episodes from Plex Media Server to MyShows.me')
@click.option('--plex-url',
              metavar='<url>',
              required=True,
              help='Plex Media Server url')
@click.option('--plex-token',
              metavar='<token>',
              required=True,
              help='Plex Media Server access token')
@click.option('--plex-section',
              metavar='<section>',
              required=True,
              help='Plex Media Server section to sync')
@click.option('--myshows-url',
              metavar='<url>',
              required=True,
              help='MyShows.Me url')
@click.option('--myshows-oauth2-url',
              metavar='<url>',
              required=True,
              help='MyShows.Me OAuth2 token endpoint')
@click.option('--myshows-client-id',
              metavar='<username>',
              required=True,
              help='MyShows.Me OAuth2 client id')
@click.option('--myshows-client-secret',
              metavar='<password>',
              required=True,
              help='MyShows.Me OAuth2 client secret')
@click.option('--myshows-auth-code',
              metavar='<password>',
              required=False,
              help='MyShows.Me OAuth2 authorization code')
@click.option('--graylog-host',
              metavar='<address>',
              required=True,
              help='Graylog address')
@click.option('--graylog-port',
              default=12201,
              show_default=True,
              metavar='<port>',
              required=True,
              help='Graylog port')
@click.option('--what-if',
              default=False,
              metavar='<boolean>',
              is_flag=True,
              help='No sync only show episodes')
def cli(plex_url, plex_token, plex_section, myshows_url, myshows_oauth2_url, myshows_client_id, myshows_client_secret, myshows_auth_code, graylog_host, graylog_port, what_if):
    myshows = MyShows(myshows_url, myshows_oauth2_url, myshows_client_id, myshows_client_secret, myshows_auth_code)
    logger = Graylog(graylog_host, graylog_port)
    try:
        plex_instance = PlexServer(plex_url, plex_token)
    except:
        print('No Plex Media Server found at {}'.format(plex_url))
        logger.log('No Plex Media Server found at {}'.format(plex_url))
        sys.exit(1)

    plex = Plex(plex_instance)
    watched_episodes = plex.get_watched_episodes(plex_section)

    for entry in watched_episodes:
        series_id = myshows.get_series_id(entry.grandparentTitle, plex_instance.library.getByKey(entry.grandparentRatingKey).year)
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
                            logger.log('{} season {} episode {} will mark as watched'.format(info['series_title'],
                                                                                             info['season'],
                                                                                             info['episode']))
                        else:
                            print('Episode with id {} not found'.format(episode_id))
                            logger.log('Episode with id {} not found'.format(episode_id))
                    else:
                        if myshows.mark_episode_as_watch(episode_id):
                            print('{} season {} episode {} mark as watched'.format(info['series_title'],
                                                                                   info['season'],
                                                                                   info['episode']))
                            logger.log('{} season {} episode {} mark as watched'.format(info['series_title'],
                                                                                        info['season'],
                                                                                        info['episode']))
            else:
                print(series_id)
                print('{} season {} episode {} not found'.format(entry.grandparentTitle,
                                                                 entry.parentIndex,
                                                                 entry.index))
                logger.log('{} season {} episode {} not found'.format(entry.grandparentTitle,
                                                                      entry.parentIndex,
                                                                      entry.index))
        else:
            print('Series {} not found'.format(entry.grandparentTitle))
            logger.log('Series {} not found'.format(entry.grandparentTitle))


if __name__ == '__main__':
    cli()
