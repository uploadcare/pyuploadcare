"""Compatibility layer for httpx / httpx2.

TODO: once Python 3.8 and 3.9 support is dropped, this module can be removed
entirely.
"""

import sys


if sys.version_info >= (3, 10):
    import httpx2 as httpx
    from httpx2 import (
        USE_CLIENT_DEFAULT,
        Auth,
        Headers,
        HTTPError,
        HTTPStatusError,
        Request,
        Response,
        UnsupportedProtocol,
    )
    from httpx2._client import Client, UseClientDefault
    from httpx2._types import (
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
    from httpx2._utils import to_bytes, to_str
else:
    import httpx
    from httpx import (
        USE_CLIENT_DEFAULT,
        Auth,
        Headers,
        HTTPError,
        HTTPStatusError,
        Request,
        Response,
        UnsupportedProtocol,
    )
    from httpx._client import Client, UseClientDefault
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
    from httpx._utils import to_bytes, to_str

__all__ = [
    "httpx",
    "USE_CLIENT_DEFAULT",
    "Auth",
    "Headers",
    "HTTPError",
    "HTTPStatusError",
    "Request",
    "Response",
    "UnsupportedProtocol",
    "Client",
    "UseClientDefault",
    "AuthTypes",
    "CookieTypes",
    "HeaderTypes",
    "QueryParamTypes",
    "RequestContent",
    "RequestData",
    "RequestFiles",
    "TimeoutTypes",
    "URLTypes",
    "to_bytes",
    "to_str",
]
