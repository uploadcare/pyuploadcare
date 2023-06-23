DEFAULT_RETRY_AFTER = 15  # in seconds


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
                response.headers.get("retry-after", DEFAULT_RETRY_AFTER)
            )
        except ValueError:
            self.wait = DEFAULT_RETRY_AFTER
        self.wait += 1


class UploadError(UploadcareException):
    """Upload errors.

    It raises when user wants to wait the result of::

        $ ucare upload_from_url --wait http://path.to/file.jpg

    """


class DuplicateFileError(UploadError):
    """
    Raised within UploadAPI.upload_from_url if check_duplicates is True
    and file was already been uploaded before)
    """

    file_id: str

    def __init__(self, message: str, file_id: str) -> None:
        super().__init__(message)
        self.file_id = file_id


class DefaultResponseClassNotDefined(Exception):
    def __init__(self) -> None:
        super().__init__("Need define default response class for API.")


class MetadataValidationError(UploadcareException):
    """
    Raised when a 'key' or 'value' of metadata did not satisfy the constraints
    """


class WebhookIsNotUnique(InvalidRequestError):
    """
    Raised while creating or updating webhook
    when pair ('project', 'target_url') is not unique
    """
