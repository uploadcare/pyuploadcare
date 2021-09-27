import socket
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

from pyuploadcare import __version__, conf
from pyuploadcare.exceptions import UploadcareHTTPStatusError


class Client(HTTPXClient):
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

    def request(
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
        try:
            response.raise_for_status()
        except HTTPStatusError as exc:
            raise UploadcareHTTPStatusError(exc.request, exc.response) from exc
        return response

    def _build_user_agent(self):
        extension_info = ""
        if conf.user_agent_extension:
            extension_info = f"; {conf.user_agent_extension}"
        return "PyUploadcare/{0}/{1} ({2}/{3}{4})".format(
            __version__,
            conf.pub_key,
            python_implementation(),
            python_version(),
            extension_info,
        )


def get_timeout(timeout):
    if timeout is not conf.DEFAULT:
        return timeout
    if conf.timeout is not conf.DEFAULT:
        return conf.timeout
    return socket.getdefaulttimeout()
