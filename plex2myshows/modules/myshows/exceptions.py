class MyshowsAPIError(Exception):
    """Root exception for all errors related to this library"""


class APIError(MyshowsAPIError):
    """An error occurred while performing a request to API"""


class ResponseParseError(MyshowsAPIError):
    """An error occurred while parse a response from API"""


class AuthError(MyshowsAPIError):
    """An error occurred while performing authorization"""
