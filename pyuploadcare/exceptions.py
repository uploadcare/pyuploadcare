# coding: utf-8


class UploadcareException(Exception):
    """Base exception class of library."""


class APIConnectionError(UploadcareException):
    """Network communication with Uploadcare errors."""


class TimeoutError(APIConnectionError):
    """Request timed out errors, e.g. when trying to store or delete."""


class AuthenticationError(UploadcareException):
    """Authentication with Uploadcare's API errors."""


