from httpx import Request, Response


class DefaultResponseClassNotDefined(Exception):
    def __init__(self) -> None:
        super().__init__("Need define default response class for API.")


class UploadCareError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class UploadCareHTTPStatusError(UploadCareError):
    def __init__(self, request: "Request", response: "Response") -> None:
        self.request = request
        self.response = response
        if response.status_code == 429:
            wait_time = response.headers.get("Retry-After")
            super().__init__(
                f"Number of seconds to wait before the next request = '{wait_time}'."
            )
        super().__init__(response.json().get("detail", None))
