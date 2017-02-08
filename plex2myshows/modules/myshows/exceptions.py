class MyshowsAPIError(Exception):
    """Root exception for all errors related to this library"""


class TransportError(MyshowsAPIError):
    """An error occurred while performing a connection to the server"""


class ProtocolError(MyshowsAPIError):
    """An error occurred while dealing with the JSON-RPC protocol"""


class AuthError(MyshowsAPIError):
    """An error occurred while performing authorization with OAuth2"""


class MyshowsOAuth2CommonError(MyshowsAPIError):
    """An error occured while use token cache file or something else"""


class MyshowsOAuth2CodeError(MyshowsAPIError):
    """An error occured while get OAuth2 token with authorization code"""


class MyshowsOAuth2TokenError(MyshowsAPIError):
    """An error occured with OAuth2 token"""
