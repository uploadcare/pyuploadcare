# coding: utf-8


class UploadCareException(Exception):
    """Base exception class of library."""


class APIConnectionError(UploadCareException):
    """Network communication with Uploadcare errors."""


class TimeoutError(APIConnectionError):
    """Request timed out errors, e.g. when trying to store or delete."""


class AuthenticationError(UploadCareException):
    """Authentication with Uploadcare's API errors."""


class APIError(UploadCareException):
    """API errors, e.g. bad json."""


class InvalidRequestError(UploadCareException, ValueError):
    """Invalid parameters errors, e.g. status 404."""
