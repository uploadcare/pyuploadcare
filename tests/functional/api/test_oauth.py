import os
import subprocess
import sys
from typing import List

import httpx2
import pytest

from pyuploadcare import Uploadcare
from pyuploadcare.api.auth import UploadcareAuth, UploadcareOAuth
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


# Uploadcare


FILE_UUID = "cdc00a7a-366f-4e0b-a942-9a7141b4004b"


class RecordingTransport:
    def __init__(self) -> None:
        self.requests: List[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if request.url.path == "/multipart/start/":
            return httpx2.Response(
                200,
                json={
                    "uuid": FILE_UUID,
                    "parts": ["https://storage.example/part1?X-Amz=sig"],
                },
            )
        if request.url.path == "/from_url/status/":
            return httpx2.Response(200, json={"status": "progress"})
        if request.url.path.startswith("/files/"):
            return httpx2.Response(200, json={"tags": []})
        return httpx2.Response(200, json={})


def make_uploadcare(transport: RecordingTransport, **kwargs) -> Uploadcare:
    uploadcare = Uploadcare(
        public_key="demopublickey", secret_key="demosecretkey", **kwargs
    )
    for client in (
        uploadcare.rest_client,
        uploadcare.upload_client,
        uploadcare.cdn_client,
    ):
        client._transport = httpx2.MockTransport(transport)
    return uploadcare


def test_uploadcare_keeps_key_pair_auth_without_oauth_token():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token=None)

    uploadcare.tags_api.get(FILE_UUID)

    assert uploadcare.oauth is None
    assert isinstance(uploadcare.rest_client.auth, UploadcareAuth)
    headers = transport.requests[0].headers
    assert headers["Authorization"].startswith("Uploadcare demopublickey:")
    assert headers["Accept"] == "application/vnd.uploadcare-v0.7+json"


def test_uploadcare_set_access_token_requires_oauth():
    uploadcare = make_uploadcare(RecordingTransport(), oauth_token=None)

    with pytest.raises(ValueError):
        uploadcare.set_access_token("token")


def test_uploadcare_rest_api_uses_oauth_token():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token="token")

    uploadcare.tags_api.get(FILE_UUID)

    headers = transport.requests[0].headers
    assert headers["Authorization"] == "Bearer token"
    # The REST API version is still requested.
    assert headers["Accept"] == "application/vnd.uploadcare-v0.7+json"


def test_uploadcare_upload_api_uses_oauth_token():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token="token")

    uploadcare.upload_api.get_upload_from_url_status("some-token")

    assert transport.requests[0].headers["Authorization"] == "Bearer token"


def test_uploadcare_cdn_never_gets_oauth_token():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token="token")

    uploadcare.url_api._client.get(
        uploadcare.url_api._build_url(FILE_UUID, suffix="detect_faces/")
    )

    assert uploadcare.cdn_client.auth is None
    assert "Authorization" not in transport.requests[0].headers


def test_uploadcare_set_access_token_applies_to_rest_and_upload():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token="old")

    assert uploadcare.set_access_token("new") == "new"
    uploadcare.tags_api.get(FILE_UUID)
    uploadcare.upload_api.get_upload_from_url_status("some-token")

    assert [r.headers["Authorization"] for r in transport.requests] == [
        "Bearer new",
        "Bearer new",
    ]


def test_multipart_chunks_never_get_oauth_token():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token="token")

    uploadcare.upload_api.multipart_upload_chunk(
        "https://storage.example/part1?X-Amz=sig", b"chunk"
    )

    request = transport.requests[0]
    assert request.url.host == "storage.example"
    assert "Authorization" not in request.headers


def test_uploadcare_reads_uploadcare_oauth_token_env():
    # Settings are read at import time, hence a fresh interpreter.
    code = (
        "from pyuploadcare import Uploadcare; "
        "print(Uploadcare(public_key='pub').oauth.access_token)"
    )
    env = {**os.environ, "UPLOADCARE_OAUTH_TOKEN": "from-env"}

    output = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert output.split() == ["from-env"]


def test_sets_public_key_header_when_given():
    server = TokenServer("token")

    make_http_client(UploadcareOAuth("token", public_key="pub"), server).get(
        URL
    )

    headers = server.requests[0].headers
    assert headers["Authorization"] == "Bearer token"
    assert headers["X-Uploadcare-Pub-Key"] == "pub"


def test_uploadcare_rest_and_upload_send_public_key_header():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token="token")

    uploadcare.tags_api.get(FILE_UUID)
    uploadcare.upload_api.get_upload_from_url_status("some-token")

    assert [r.headers["X-Uploadcare-Pub-Key"] for r in transport.requests] == [
        "demopublickey",
        "demopublickey",
    ]


def test_uploadcare_cdn_and_chunks_send_no_public_key_header():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token="token")

    uploadcare.url_api._client.get(
        uploadcare.url_api._build_url(FILE_UUID, suffix="detect_faces/")
    )
    uploadcare.upload_api.multipart_upload_chunk(
        "https://storage.example/part1?X-Amz=sig", b"chunk"
    )

    for request in transport.requests:
        assert "X-Uploadcare-Pub-Key" not in request.headers


def test_uploadcare_key_pair_mode_sends_no_public_key_header():
    transport = RecordingTransport()
    uploadcare = make_uploadcare(transport, oauth_token=None)

    uploadcare.tags_api.get(FILE_UUID)

    assert "X-Uploadcare-Pub-Key" not in transport.requests[0].headers
