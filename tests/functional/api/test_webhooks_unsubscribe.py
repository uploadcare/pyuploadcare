"""``WebhooksAPI.unsubscribe`` and ``Uploadcare.unsubscribe_webhook``.

https://uploadcare.com/docs/api/rest/webhook/unsubscribe/
"""

import json

import httpx2
import pytest

from pyuploadcare import Uploadcare
from pyuploadcare.exceptions import (
    AuthenticationError,
    InvalidParamError,
    InvalidRequestError,
)


UNSUBSCRIBE_URL = "https://api.uploadcare.com/webhooks/unsubscribe/"
TARGET_URL = "https://example.com/hooks/uploaded"


class FakeServer:
    """Answers ``unsubscribe`` with ``status``."""

    def __init__(self, status: int = 204) -> None:
        self.status = status
        self.requests: list[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if self.status == 204:
            return httpx2.Response(204)
        return httpx2.Response(self.status, json={"detail": "error"})


def make_uploadcare(server: FakeServer, **kwargs) -> Uploadcare:
    kwargs.setdefault("secret_key", "demosecretkey")
    uploadcare = Uploadcare(public_key="demopublickey", retry_throttled=0, **kwargs)
    uploadcare.rest_client._transport = httpx2.MockTransport(server)
    return uploadcare


# Unsubscribe


def test_unsubscribe_sends_delete_with_json_body():
    server = FakeServer()
    uploadcare = make_uploadcare(server)

    uploadcare.unsubscribe_webhook(TARGET_URL)

    (request,) = server.requests
    assert request.method == "DELETE"
    assert str(request.url) == UNSUBSCRIBE_URL
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == {"target_url": TARGET_URL}


def test_unsubscribe_low_level():
    server = FakeServer()
    uploadcare = make_uploadcare(server)

    uploadcare.webhooks_api.unsubscribe(TARGET_URL)

    (request,) = server.requests
    assert str(request.url) == UNSUBSCRIBE_URL


@pytest.mark.parametrize(
    "target_url",
    [
        "",
        None,
        42,
        "example.com/hooks",
        "/hooks/uploaded",
        "ftp://example.com/hooks",
        "javascript:alert(1)",
        "https://",
    ],
)
def test_unsubscribe_rejects_invalid_target_url(target_url):
    server = FakeServer()
    uploadcare = make_uploadcare(server)

    with pytest.raises(InvalidParamError):
        uploadcare.unsubscribe_webhook(target_url)

    assert server.requests == []


@pytest.mark.parametrize(
    "status,error",
    [
        (400, InvalidRequestError),
        (404, InvalidRequestError),
        (401, AuthenticationError),
        (403, AuthenticationError),
    ],
)
def test_unsubscribe_errors(status, error):
    uploadcare = make_uploadcare(FakeServer(status=status))

    with pytest.raises(error):
        uploadcare.unsubscribe_webhook(TARGET_URL)


def test_unsubscribe_signs_request_with_key_pair():
    server = FakeServer()
    uploadcare = make_uploadcare(server)

    uploadcare.unsubscribe_webhook(TARGET_URL)

    headers = server.requests[0].headers
    assert headers["Authorization"].startswith("Uploadcare demopublickey:")
    assert headers["Accept"] == "application/vnd.uploadcare-v0.7+json"
    assert "Date" in headers
