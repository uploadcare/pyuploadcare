__all__ = ["Client"]

import logging
import sys
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


PY37_PLUS = sys.version_info[:2] > (3, 6)
PY36 = not PY37_PLUS


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
        content: typing.Optional[RequestContent] = None,
        data: typing.Optional[RequestData] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[QueryParamTypes] = None,
        headers: typing.Optional[HeaderTypes] = None,
        cookies: typing.Optional[CookieTypes] = None,
        auth: typing.Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        follow_redirects: typing.Optional[bool] = None,
        allow_redirects: typing.Optional[bool] = None,
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
            follow_redirects=follow_redirects,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

    def request(  # type: ignore # noqa: C901
        self,
        method: str,
        url: URLTypes,
        *,
        content: typing.Optional[RequestContent] = None,
        data: typing.Optional[RequestData] = None,
        files: typing.Optional[RequestFiles] = None,
        json: typing.Any = None,
        params: typing.Optional[QueryParamTypes] = None,
        headers: typing.Optional[HeaderTypes] = None,
        cookies: typing.Optional[CookieTypes] = None,
        auth: typing.Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        follow_redirects: typing.Optional[bool] = None,
        allow_redirects: typing.Optional[bool] = None,
        timeout: typing.Union[
            TimeoutTypes, UseClientDefault
        ] = USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> Response:
        """
        `allow_redirects` is for compatibility with versions for Python 3.6 only
         should use `follow_redirects` instead

        `redirecting` is `True` by default (look at `_handle_httpx_arguments` method)
        if `allow_redirects` is set - its value is used (deprecated for Python 3.7 and newer)
        if `follow_redirects` is also set - ValueError will be rised

        arguments are passed by into `_perform_request`,
        result value of `redirecting` is computed there
        """

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
                    follow_redirects=follow_redirects,
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

    def _handle_httpx_arguments(  # noqa: max-complexity: 6
        self,
        follow_redirects: typing.Optional[bool] = None,
        allow_redirects: typing.Optional[bool] = None,
    ) -> bool:
        """
        Encapsulate smooth updating for httpx dependency:
         - using of `allow_redirects` is allowed,
           but that argument will be deleted in the next major version
         - using of `follow_redirects` is allowed when
           `allow_redirects` is not set
        """
        redirecting = True

        if allow_redirects is not None and follow_redirects is not None:
            raise ValueError(
                "You must not use these arguments together:"
                "`allow_redirects` and `follow_redirects`"
            )

        if allow_redirects is not None:
            logger.warning(
                "Argument `allow_redirects` is deprecated "
                "and will be removed in version 4.x."
                "Use `follow_redirects` instead"
            )
            redirecting = allow_redirects

        if follow_redirects is not None:
            redirecting = follow_redirects

        return redirecting

    def _perform_response(  # noqa: max-complexity: 6
        self, response: Response
    ) -> Response:
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

    def _perform_request(  # noqa: C901
        self,
        method: str,
        url: URLTypes,
        content: typing.Optional[RequestContent] = None,
        data: typing.Optional[RequestData] = None,
        files: typing.Optional[RequestFiles] = None,
        json: typing.Any = None,
        params: typing.Optional[QueryParamTypes] = None,
        headers: typing.Optional[HeaderTypes] = None,
        cookies: typing.Optional[CookieTypes] = None,
        auth: typing.Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        follow_redirects: typing.Optional[bool] = None,
        allow_redirects: typing.Optional[bool] = None,
        timeout: typing.Union[
            TimeoutTypes, UseClientDefault
        ] = USE_CLIENT_DEFAULT,
    ):
        logger.debug(
            f"sent: method: {method}; path: {url}; headers: {headers}; "
            f"json: {json}; data: {data}; content: {str(content)}"
        )

        redirecting = self._handle_httpx_arguments(
            allow_redirects=allow_redirects,
            follow_redirects=follow_redirects,
        )

        kwargs = dict(
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            timeout=timeout,
        )

        if PY36:
            kwargs["allow_redirects"] = redirecting
        elif PY37_PLUS:
            kwargs["follow_redirects"] = redirecting
        else:
            raise ValueError(
                "Unexpected set of Python version. Check the setup"
            )

        response = super().request(method, url, **kwargs)  # type: ignore
        performed_response = self._perform_response(response)

        return performed_response

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
