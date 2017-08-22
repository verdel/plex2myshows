class MyshowsAPIError(Exception):
    """Root exception for all errors related to this library"""


class APIError(MyshowsAPIError):
    """An error occurred while performing a request to API"""


class AuthError(MyshowsAPIError):
    """An error occurred while performing authorization"""
