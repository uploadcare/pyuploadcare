from typing import List

import httpx2
import pytest

from pyuploadcare.api.auth import UploadcareOAuth
from pyuploadcare.api.client import Client
from pyuploadcare.exceptions import AuthenticationError


URL = "https://api.uploadcare.com/projects/"
PAGE = {"next": None, "previous": None, "total": 0, "per_page": 20}


class TokenServer:
    """Accepts only `valid_token`, records the requests it got."""

    def __init__(self, valid_token: str) -> None:
        self.valid_token = valid_token
        self.requests: List[httpx2.Request] = []

    @property
    def tokens(self) -> List[str]:
        return [
            request.headers["Authorization"].removeprefix("Bearer ")
            for request in self.requests
        ]

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if request.headers["Authorization"] != f"Bearer {self.valid_token}":
            return httpx2.Response(401, json={"code": "authentication_error"})
        return httpx2.Response(200, json={**PAGE, "results": []})


def make_http_client(auth: UploadcareOAuth, server: TokenServer) -> Client:
    return Client(auth=auth, transport=httpx2.MockTransport(server))


def test_sets_bearer_header_only():
    server = TokenServer("token")

    make_http_client(UploadcareOAuth("token"), server).get(URL)

    headers = server.requests[0].headers
    assert headers["Authorization"] == "Bearer token"
    # API specific headers are left to the client of each API.
    assert headers.get("Accept", "*/*") == "*/*"


@pytest.mark.parametrize("token", [None, "", "   ", 42])
def test_rejects_empty_token(token):
    with pytest.raises(ValueError):
        UploadcareOAuth(token)


def test_accepts_bytes_token():
    assert UploadcareOAuth(b"token").access_token == "token"


def test_set_access_token_replaces_token_for_following_requests():
    server = TokenServer("new")
    auth = UploadcareOAuth("old")
    client = make_http_client(auth, server)

    with pytest.raises(AuthenticationError):
        client.get(URL)

    assert auth.set_access_token("new") == "new"
    client.get(URL)

    assert auth.access_token == "new"
    assert server.tokens == ["old", "new"]


@pytest.mark.parametrize("token", [None, "", "   "])
def test_set_empty_access_token_keeps_old_one(token):
    auth = UploadcareOAuth("old")

    with pytest.raises(ValueError):
        auth.set_access_token(token)

    assert auth.access_token == "old"


def test_401_is_not_retried():
    server = TokenServer("new")

    with pytest.raises(AuthenticationError):
        make_http_client(UploadcareOAuth("old"), server).get(URL)

    assert server.tokens == ["old"]


def test_sets_public_key_header_when_given():
    server = TokenServer("token")

    make_http_client(UploadcareOAuth("token", public_key="pub"), server).get(
        URL
    )

    headers = server.requests[0].headers
    assert headers["Authorization"] == "Bearer token"
    assert headers["X-Uploadcare-Pub-Key"] == "pub"
