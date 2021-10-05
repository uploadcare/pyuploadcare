import logging
import time
import typing
from platform import python_implementation, python_version

from httpx import USE_CLIENT_DEFAULT, HTTPStatusError, Response
from httpx._client import Client as HTTPXClient
from httpx._client import UseClientDefault
from httpx._types import (
    AuthTypes,
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
)

from pyuploadcare import __version__
from pyuploadcare.exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    ThrottledRequestError,
)


logger = logging.getLogger("pyuploadcare")


class Client(HTTPXClient):
    def __init__(self, *args, **kwargs):
        self.user_agent_extension = kwargs.pop("user_agent_extension", None)
        self.retry_throttled = kwargs.pop("retry_throttled", None)
        self.public_key = kwargs.pop("public_key", None)

        super().__init__(*args, **kwargs)

    def delete_with_payload(
        self,
        url: URLTypes,
        *,
        content: RequestContent = None,
        data: RequestData = None,
        json: typing.Any = None,
        params: QueryParamTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        auth: typing.Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        allow_redirects: bool = True,
        timeout: typing.Union[
            TimeoutTypes, UseClientDefault
        ] = USE_CLIENT_DEFAULT,
    ) -> Response:
        """
        Send a `DELETE` request with payload.

        **Parameters**: See `httpx.request`.
        """
        return self.request(
            "DELETE",
            url,
            content=content,
            data=data,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

    def request(  # noqa: C901
        self,
        method: str,
        url: URLTypes,
        *,
        content: RequestContent = None,
        data: RequestData = None,
        files: RequestFiles = None,
        json: typing.Any = None,
        params: QueryParamTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        auth: typing.Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        allow_redirects: bool = True,
        timeout: typing.Union[
            TimeoutTypes, UseClientDefault
        ] = USE_CLIENT_DEFAULT,
    ) -> Response:
        if not headers:
            headers = {}  # type: ignore

        headers["User-Agent"] = self._build_user_agent()  # type: ignore

        retry_throttled = self.retry_throttled

        while True:
            try:
                return self._perform_request(
                    method,
                    url,
                    content=content,
                    data=data,
                    files=files,
                    json=json,
                    params=params,
                    headers=headers,
                    cookies=cookies,
                    auth=auth,
                    allow_redirects=allow_redirects,
                    timeout=timeout,
                )
            except ThrottledRequestError as e:
                if retry_throttled > 0:
                    logger.debug(f"Throttled, retry in {e.wait} seconds")
                    time.sleep(e.wait)
                    retry_throttled -= 1
                    continue
                else:
                    raise

    def _perform_request(  # noqa: C901
        self,
        method: str,
        url: URLTypes,
        content: RequestContent = None,
        data: RequestData = None,
        files: RequestFiles = None,
        json: typing.Any = None,
        params: QueryParamTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        auth: typing.Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        allow_redirects: bool = True,
        timeout: typing.Union[
            TimeoutTypes, UseClientDefault
        ] = USE_CLIENT_DEFAULT,
    ):
        logger.debug(
            f"sent: method: {method}; path: {url}; headers: {headers}; "
            f"json: {json}; data: {data}; content: {str(content)}"
        )
        response = super().request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

        logger.debug(
            f"got: status_code: {response.status_code}; "
            f"content: {str(response.content)}; headers: {response.headers}"
        )

        if response.status_code in (401, 403):
            raise AuthenticationError(response.content.decode())

        if response.status_code in (400, 404):
            raise InvalidRequestError(response.content.decode())

        if response.status_code == 429:
            raise ThrottledRequestError(response)

        try:
            response.raise_for_status()
        except HTTPStatusError:
            raise APIError(response.content.decode())

        return response

    def _build_user_agent(self):
        extension_info = ""
        if self.user_agent_extension:
            extension_info = f"; {self.user_agent_extension}"
        return "PyUploadcare/{0}/{1} ({2}/{3}{4})".format(
            __version__,
            self.public_key,
            python_implementation(),
            python_version(),
            extension_info,
        )
