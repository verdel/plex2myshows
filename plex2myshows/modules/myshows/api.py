import requests
import random
import sys
try:
    import simplejson as json
except ImportError:
    import json
from .oauth2 import OAuth2
from .exceptions import TransportError, ProtocolError, AuthError


class MyShows(object):
    def __init__(self, api_url, oauth2_url, client_id, client_secret, auth_code, token_path=None):
        self.api_url = api_url
        token_handler = OAuth2(client_id, client_secret, oauth2_url, auth_code, token_path=token_path)
        try:
            self.token = token_handler.get_token()
        except Exception as exc:
            raise AuthError('[OAuth2 error] Can`t get Myshows APIv2 auth token. {}'.format(exc))

    def serialize(self, method_name, params):
        """Generate the raw JSON message to be sent to the server"""
        data = {'jsonrpc': '2.0', 'method': method_name}
        if params:
            data['params'] = params
            # some JSON-RPC servers complain when receiving str(uuid.uuid4()). Let's pick something simpler.
            data['id'] = random.randint(1, sys.maxsize)
            return json.dumps(data)

    def send_request(self, method_name, params):
        """Issue the HTTP request to the server and return the method result (if not a notification)"""
        request_head = {'Authorization': "Bearer {}".format(self.token), 'Content-Type': "application/json", 'Accept': "application/json"}
        request_body = self.serialize(method_name, params)

        try:
            response = requests.post(self.api_url, data=request_body, headers=request_head)
        except requests.RequestException as requests_exception:
            raise TransportError('[API error] Error calling method {}'.format(method_name), requests_exception)

        if response.status_code != requests.codes.ok:
            raise TransportError('[API error] {}'.format(response.status_code))

        try:
            parsed = response.json()
        except ValueError as value_error:
            raise TransportError('[API error] Cannot deserialize response body', value_error)
        return self.parse_result(parsed)

    @staticmethod
    def parse_result(result):
        """Parse the data returned by the server according to the JSON-RPC spec. Try to be liberal in what we accept."""
        if not isinstance(result, dict):
            raise ProtocolError('[API error] Response is not a dictionary')
        if result.get('error'):
            code = result['error'].get('code', '')
            message = result['error'].get('message', '')
            raise ProtocolError('[API error] {}'.format(code), message, result)
        elif 'result' not in result:
            raise ProtocolError('[API error] Response without a result field')
        else:
            return result['result']

    def get_series_id(self, title, year):
        series = self.send_request('shows.Search', {'query': title})
        if len(series) > 1:
            for item in series:
                if (item['titleOriginal'].lower() == title.lower() or item['title'].lower() == title.lower()) and item['year'] == year:
                    series_id = item['id']
        else:
            series_id = series[0]['id']
        return series_id

    def get_episode_id(self, series_id, season_number, episode_number):
        episodes = self.send_request('shows.GetById', {'showId': series_id, 'withEpisodes': True})
        for episode in episodes['episodes']:
            if episode['seasonNumber'] == int(season_number) and episode['episodeNumber'] == int(episode_number):
                return episode['id']
        else:
            return None

    def get_watched_episodes_id(self, series_id):
        watched_episodes = self.send_request('profile.Episodes', {'showId': series_id})
        if len(watched_episodes) > 0:
            return [item['id'] for item in watched_episodes]
        else:
            return None

    def get_episode_info(self, episode_id):
        episode_info = self.send_request('shows.Episode', {'id': episode_id})
        episode_season_number = episode_info['seasonNumber']
        episode_number = episode_info['episodeNumber']
        series_id = episode_info['showId']
        series_title = self.send_request('shows.GetById', {'showId': series_id, 'withEpisodes': False})
        return {'series_title': series_title['titleOriginal'], 'season': episode_season_number, 'episode': episode_number}

    def mark_episode_as_watch(self, episode_id):
        self.send_request('manage.CheckEpisode', {'id': episode_id})
        return True
