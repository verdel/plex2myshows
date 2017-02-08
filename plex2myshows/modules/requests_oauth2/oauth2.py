import requests
from urllib import quote
from urlparse import parse_qs
import pickle
from datetime import datetime
try:
    import simplejson as json
except ImportError:
    import json


class MyshowsOAuth2Error(Exception):
    """Root exception for all errors related to this library"""


class AuthError(MyshowsOAuth2Error):
    """An error occurred while performing a connection to the server"""


class CacheError(MyshowsOAuth2Error):
    """An error occurred while performing a connection to the server"""


class OAuth2(object):
    authorization_url = '/oauth/authorize'
    token_url = '/oauth/token'
    token_path = '/tmp/.myshows_token'

    def __init__(self, client_id, client_secret, site, auth_code=None, token_path=None, authorization_url=None, token_url=None):
        """
        Initializes the hook with OAuth2 parameters
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.site = site
        self.auth_code = auth_code
        if authorization_url is not None:
            self.authorization_url = authorization_url
        if token_url is not None:
            self.token_url = token_url
        if token_path is not None:
            self.token_path = token_path

    def get_token(self):
        try:
            with open(self.token_path, 'r') as token_file:
                token = pickle.load(token_file)
        except Exception:
            token = {}
        keys = ('access_token', 'creation_at', 'expires_in', 'refresh_token')
        if all(key in token for key in keys):
            if (datetime.now() - token['creation_at']).seconds < int(token['expires_in']):
                token = token['access_token']
            else:
                token = self.__refresh_token(token['refresh_token'])
        else:
            token = self.__get_token_from_url()

        return token

    def __get_token_from_url(self, **kwargs):
        """
        Requests an access token
        """
        authorization_url = "%s%s" % (self.site, quote(self.authorization_url))
        token_url = "%s%s" % (self.site, quote(self.token_url))

        if not self.auth_code:
            raise AuthError('Please visit url {}?response_type=code&client_id={}&scope=basic and set --myshows-auth-code option.'.format(authorization_url, self.client_id))

        data = {'client_id': self.client_id, 'client_secret': self.client_secret, 'grant_type': 'authorization_code', 'code': self.auth_code}
        data.update(kwargs)
        response = requests.post(token_url, data=data)

        if isinstance(response.content, basestring):
            try:
                content = json.loads(response.content)
            except ValueError:
                content = parse_qs(response.content)
        else:
            content = response.content

        if 'access_token' in content:
            with open(self.token_path, 'w+') as token_file:
                pickle.dump({'access_token': content['access_token'], 'creation_at': datetime.now(), 'expires_in': content['expires_in'], 'refresh_token': content['refresh_token']}, token_file)
                return content['access_token']
        elif 'error_description' in content and content['error_description'] == u"Authorization code doesn't exist or is invalid for the client":
            raise AuthError('Please visit url {}?response_type=code&client_id={}&scope=basic and set --myshows-auth-code option.'.format(authorization_url, self.client_id))
        else:
            raise AuthError(content)

    def __refresh_token(self, refresh_token):
        """
        Requests an access token
        """
        url = "%s%s" % (self.site, quote(self.token_url))
        data = {'client_id': self.client_id, 'client_secret': self.client_secret, 'grant_type': 'refresh_token', 'refresh_token': refresh_token}
        response = requests.post(url, data=data)

        if isinstance(response.content, basestring):
            try:
                content = json.loads(response.content)
            except ValueError:
                content = parse_qs(response.content)
        else:
            content = response.content

        if 'access_token' in content:
            with open(self.token_path, 'w+') as token_file:
                pickle.dump({'access_token': content['access_token'], 'creation_at': datetime.now(), 'expires_in': content['expires_in'], 'refresh_token': content['refresh_token']}, token_file)
                return content['access_token']
        else:
            raise AuthError(content)
