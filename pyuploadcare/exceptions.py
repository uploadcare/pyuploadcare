# coding: utf-8


class UploadcareException(Exception):
    """Base exception class of library."""


class APIConnectionError(UploadcareException):
    """Network communication with Uploadcare errors."""


class TimeoutError(UploadcareException):
    """Timed out errors.

    It raises when user wants to wait the result of api requests, e.g.::

        $ ucare store --wait 6c5e9526-b0fe-4739-8975-72e8d5ee6342

    """


class AuthenticationError(UploadcareException):
    """Authentication with Uploadcare's API errors."""


class APIError(UploadcareException):
    """API errors, e.g. bad json."""


class InvalidRequestError(UploadcareException, ValueError):
    """Invalid parameters errors, e.g. status 404."""


class UploadError(UploadcareException):
    """Upload errors.

    It raises when user wants to wait the result of::

        $ ucare upload_from_url --wait http://path.to/file.jpg

    """
