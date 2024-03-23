import hashlib
import hmac
from datetime import datetime, timezone
from typing import Generator, Union

from httpx import Auth, Request, Response
from httpx._utils import to_bytes, to_str


class AuthBase(Auth): ...


class UploadcareSimpleAuth(AuthBase):
    def __init__(
        self,
        public_key: Union[str, bytes],
        secret_key: Union[str, bytes],
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
        public_key: Union[str, bytes],
        secret_key: Union[str, bytes],
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
        public_key: Union[str, bytes],
        secret_key: Union[str, bytes],
        formated_date_time: str = "",
    ) -> str:
        content_md5 = hashlib.md5(request.read()).hexdigest()
        content_type = request.headers.get("Content-Type")
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
