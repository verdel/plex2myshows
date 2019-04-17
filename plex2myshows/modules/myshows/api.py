import requests
import hashlib
from .exceptions import AuthError, APIError, ResponseParseError


class MyShows(object):
    def __init__(self, api_url, username, password):
        self.api_url = api_url
        self.cookie = self.__auth(username, password)

    def __auth(self, username, password):
        api = requests.get('{}/profile/login'.format(self.api_url),
                           params={'login': username,
                                   'password': hashlib.md5(password).hexdigest()})
        if api.status_code != 200:
            raise AuthError('[Myshows.me auth error] Invalid username or password.')
        else:
            return api.cookies

    def __send_request(self, method_path):
        """Issue the HTTP request to the server and return the method result (if not a notification)"""
        try:
            response = requests.get('{}/{}'.format(self.api_url, method_path), cookies=self.cookie)
        except requests.RequestException as requests_exception:
            raise APIError('[API error] Error calling method {}'.format(method_path), requests_exception)

        if response.status_code != requests.codes.ok:
            raise APIError('[API error] {}'.format(response.status_code))
        try:
            parsed = response.json()
        except ValueError as value_error:
            raise ResponseParseError('[Response Parse Error] Cannot deserialize response body', value_error)
        return parsed

    def get_series_id(self, title, year):
        try:
            series = self.__send_request('shows/search/?q={}'.format(title))
        except:
            return None

        if len(series) == 1:
            series_id = series.values()[0]['id']
        elif len(series) > 1:
            series_id = None
            for item in series.values():
                if item['title']:
                    item['title'] = item['title'].lower()
                if item['ruTitle']:
                    item['ruTitle'] = item['ruTitle'].lower()

                if (item['title'] == title.lower() or item['ruTitle'] == title.lower()) and item['year'] == year:
                    series_id = item['id']
                    break
        else:
            return None

        return series_id

    def get_series_by_id(self, series_id):
        try:
            series = self.__send_request('shows/{}'.format(series_id))
        except:
            return None
        if len(series) > 0:
            return series
        else:
            return None

    def get_episode_id(self, series_id, season_number, episode_number):
        try:
            episodes = self.__send_request('shows/{}'.format(series_id))
        except:
            return None
        if episodes:
            for episode in episodes['episodes'].values():
                if episode['seasonNumber'] == int(season_number) and episode['episodeNumber'] == int(episode_number):
                    return episode['id']
        else:
            return None

    def get_watched_episodes_id(self, series_id):
        try:
            watched_episodes = self.__send_request('profile/shows/{}/'.format(series_id))
        except:
            return None
        if len(watched_episodes) > 0:
            return [item['id'] for item in watched_episodes.values()]
        else:
            return None

    def get_episode_info(self, episode_id):
        try:
            episode_info = self.__send_request('episodes/{}'.format(episode_id))
        except:
            return None
        episode_season_number = episode_info['seasonNumber']
        episode_number = episode_info['episodeNumber']
        series_id = episode_info['showId']
        series_title = self.get_series_by_id(series_id)
        return {'series_title': series_title['title'], 'season': episode_season_number, 'episode': episode_number}

    def mark_episode_as_watch(self, episode_id):
        try:
            self.__send_request('profile/episodes/check/{}'.format(episode_id))
        except APIError:
            return False
        except ResponseParseError:
            return True
        else:
            return True
