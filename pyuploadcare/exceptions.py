class UploadcareException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


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
    """Invalid service parameters errors, e.g status 404"""


class InvalidParamError(InvalidRequestError):
    """Invalid parameters errors, e.g. invalid UUID"""


class ThrottledRequestError(UploadcareException):
    """Raised when request was throttled."""

    def __init__(self, response):
        try:
            self.wait = int(
                response.headers.get("x-throttle-wait-seconds", 15)
            )
        except ValueError:
            self.wait = 15
        self.wait += 1


class UploadError(UploadcareException):
    """Upload errors.

    It raises when user wants to wait the result of::

        $ ucare upload_from_url --wait http://path.to/file.jpg

    """


class DefaultResponseClassNotDefined(Exception):
    def __init__(self) -> None:
        super().__init__("Need define default response class for API.")
