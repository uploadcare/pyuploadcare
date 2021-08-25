from typing import Any, Union

from httpx import USE_CLIENT_DEFAULT, Response
from httpx._client import Client as HTTPXClient
from httpx._client import UseClientDefault
from httpx._types import (
    AuthTypes,
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    TimeoutTypes,
    URLTypes,
)


class Client(HTTPXClient):
    def delete_with_payload(
        self,
        url: URLTypes,
        *,
        content: RequestContent = None,
        data: RequestData = None,
        json: Any = None,
        params: QueryParamTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        auth: Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        allow_redirects: bool = True,
        timeout: Union[TimeoutTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
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
