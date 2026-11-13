import hashlib
import hmac
from collections.abc import Generator
from datetime import datetime, timezone

from httpx2 import Auth, Request, Response
from httpx2._utils import to_bytes, to_str


class AuthBase(Auth): ...


class UploadcareSimpleAuth(AuthBase):
    def __init__(
        self,
        public_key: str | bytes,
        secret_key: str | bytes,
        api_version: str,
    ) -> None:
        self.public_key = public_key
        self.secret_key = secret_key
        self.api_version = api_version

    def auth_flow(
        self, request: Request
    ) -> Generator[Request, Response, None]:
        if "Content-Type" not in request.headers:
            request.headers["Content-Type"] = "application/json"

        request.headers["Accept"] = (
            f"application/vnd.uploadcare-v{self.api_version}+json"
        )
        request.headers["Authorization"] = self._build_auth_header(
            request, self.public_key, self.secret_key
        )
        yield request

    def _build_auth_header(
        self,
        request: Request,
        public_key: str | bytes,
        secret_key: str | bytes,
        formated_date_time: str = "",
    ) -> str:
        credentials = f"{public_key!s}:{secret_key!s}"
        return f"Uploadcare.Simple {credentials}"


class UploadcareAuth(UploadcareSimpleAuth):
    def auth_flow(
        self, request: Request
    ) -> Generator[Request, Response, None]:
        formated_date_time = self._formated_date_time()

        if "Content-Type" not in request.headers:
            request.headers["Content-Type"] = "application/json"

        request.headers["Accept"] = (
            f"application/vnd.uploadcare-v{self.api_version}+json"
        )
        request.headers["Authorization"] = self._build_auth_header(
            request, self.public_key, self.secret_key, formated_date_time
        )
        request.headers["Date"] = formated_date_time
        yield request

    def _formated_date_time(self):
        return datetime.now(timezone.utc).strftime(
            "%a, %d %b %Y, %H:%M:%S GMT"
        )

    def _build_auth_header(
        self,
        request: Request,
        public_key: str | bytes,
        secret_key: str | bytes,
        formated_date_time: str = "",
    ) -> str:
        content_md5 = hashlib.md5(request.read()).hexdigest()
        content_type = request.headers.get("Content-Type") or ""
        uri = to_str(request.url.raw_path)
        sign_string = "\n".join(
            [
                request.method,
                content_md5,
                content_type,
                formated_date_time,
                uri,
            ]
        )
        signature = hmac.new(
            to_bytes(secret_key), to_bytes(sign_string), hashlib.sha1
        ).hexdigest()
        credentials = f"{public_key!s}:{signature!s}"
        return f"Uploadcare {credentials}"


class UploadcareOAuth(AuthBase):
    """OAuth 2.0 access token auth: ``Authorization: Bearer <token>``.

    Obtaining and refreshing the token is up to the caller; replace the
    token used for the following requests with ``set_access_token()``::

        >>> auth = UploadcareOAuth("<access-token>")
        >>> auth.set_access_token("<new-access-token>")

    With ``public_key`` set, requests also carry it in
    ``X-Uploadcare-Pub-Key``, which the REST and Upload APIs need to know the
    project. APIs that take the public key in the URL, such as the Project
    API, need no ``public_key`` here.

    Other headers that differ between APIs, such as ``Accept``, are up to the
    client of a particular API.
    """

    PUBLIC_KEY_HEADER = "X-Uploadcare-Pub-Key"

    def __init__(
        self,
        access_token: str | bytes,
        public_key: str | None = None,
    ) -> None:
        self._access_token = self._validate_token(access_token)
        self.public_key = public_key

    @staticmethod
    def _validate_token(access_token: str | bytes | None) -> str:
        if isinstance(access_token, bytes):
            access_token = to_str(access_token)
        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("access token must be a non-empty string")
        return access_token.strip()

    @property
    def access_token(self) -> str:
        return self._access_token

    def set_access_token(self, access_token: str | bytes) -> str:
        """Replace the access token and return the new one.

        Requests already in flight keep the token they were sent with.
        """
        self._access_token = self._validate_token(access_token)
        return self._access_token

    def auth_flow(
        self, request: Request
    ) -> Generator[Request, Response, None]:
        request.headers["Authorization"] = f"Bearer {self._access_token}"
        if self.public_key:
            request.headers[self.PUBLIC_KEY_HEADER] = self.public_key
        yield request
