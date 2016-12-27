#!/usr/bin/env python
from plexapi.server import PlexServer
import requests
import hashlib
import logging
import graypy
import click
import sys


class Plex(object):
    def __init__(self, plex):
        self.plex = plex

    def _get_all_episodes(self, section_name):
        all_episodes =  set(self.plex.library.section(section_name).searchEpisodes())
        return all_episodes

    def _get_unwatched_episodes(self, section_name):
        unwatched_episodes = set(self.plex.library.section(section_name).searchEpisodes(unwatched=True))
        return unwatched_episodes

    def get_watched_episodes(self, section_name):
        all_episodes = self._get_all_episodes(section_name)
        all_episodes_id = set([item.ratingKey for item in all_episodes])
        unwatched_episodes = self._get_unwatched_episodes(section_name)
        unwatched_episodes_id = set([item.ratingKey for item in unwatched_episodes])
        watched_episodes_id = all_episodes_id.difference(unwatched_episodes_id)
        watched_episodes = [item for item in all_episodes if item.ratingKey in watched_episodes_id]
        return watched_episodes


class MyShows(object):
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = hashlib.md5(password).hexdigest()
        api = requests.get('{}/profile/login'.format(self.url),
                           params={'login': self.username,
                           'password': self.password})
        if api.status_code != 200:
            print('Wrong username or password for myshows.me')
            sys.exit(1)
        else:
            self.cookies = api.cookies

    def get_series_id(self, title, year):
        series = requests.get('{}/shows/search/'.format(self.url),
                              params={'q': title},
                              cookies=self.cookies)

        if series.status_code != 200:
            print('{} is not found on myshows.me'.format(title))
            return None

        else:
            if len(series.json()) > 1:
                for item in series.json().values():
                    if item['title'].lower() == title.lower() and item['year'] == year:
                        series_id = item['id']
            else:
                series_id = series.json().values()[0]['id']
            return series_id

    def get_episode_id(self, series_id, season_number, episode_number):
        episodes = requests.get('{}/shows/{}'.format(self.url, series_id),
                                cookies=self.cookies)
        if episodes.status_code == 200:
            for episode in episodes.json()['episodes'].values():
                if episode['seasonNumber'] == int(season_number) and episode['episodeNumber'] == int(episode_number):
                    return episode['id']
        else:
            return None

    def get_watched_episodes_id(self, series_id):
        watched_episodes = requests.get('{}/profile/shows/{}/'.format(self.url, series_id),
                                        cookies=self.cookies)
        if watched_episodes.status_code == 200:
            watched_episodes = watched_episodes.json()
            if len(watched_episodes) > 0:
                return watched_episodes.keys()
            else:
                return None
        else:
            return None

    def get_episode_info(self, episode_id):
        episode_info = requests.get('{}/episodes/{}'.format(self.url, episode_id),
                                    cookies=self.cookies)
        if episode_info.status_code == 200:
            episode_info = episode_info.json()
        else:
            return None

        episode_season_number = episode_info['seasonNumber']
        episode_number = episode_info['episodeNumber']
        series_id = episode_info['showId']
        series_title = requests.get('{}/shows/{}'.format(self.url, series_id),
                                        cookies=self.cookies).json()['title']
        return {'series_title':series_title, 'season': episode_season_number, 'episode': episode_number}

    def mark_episode_as_watch(self, episode_id):
        set_episode_status = requests.get('{}/profile/episodes/check/{}'.format(self.url, episode_id),
                                      cookies=self.cookies)
        if set_episode_status.status_code == 200:
            return True


class Graylog(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.my_logger = logging.getLogger('plex2myshows')
        self.my_logger.setLevel(logging.ERROR)

        self.grayloghandler = graypy.GELFHandler(self.host, self.port)
        self.my_logger.addHandler(self.grayloghandler)
        self.my_adapter = logging.LoggerAdapter(self.my_logger,
                                                {'tag': 'plex2myshows'})

    def log(self, msg):
        self.my_adapter.error(msg)


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
@click.option('--myshows-username',
              metavar='<username>',
              required=True,
              help='MyShows.Me username')
@click.option('--myshows-password',
              metavar='<password>',
              required=True,
              help='MyShows.Me password')
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
def cli(plex_url, plex_token, plex_section, myshows_url, myshows_username, myshows_password, graylog_host, graylog_port, what_if):
    myshows = MyShows(myshows_url, myshows_username, myshows_password)
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
                watched_episodes = myshows.get_watched_episodes_id(series_id)
                if not watched_episodes or str(episode_id) not in watched_episodes:
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