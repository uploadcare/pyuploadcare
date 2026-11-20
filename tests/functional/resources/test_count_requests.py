"""Request shape assertions for ``count()`` on resource lists.

Regression tests for https://github.com/uploadcare/pyuploadcare/issues/355:
filters used to be sent as a single stringified ``query_parameters`` key.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest


FILES_URL = "https://api.uploadcare.com/files/"
GROUPS_URL = "https://api.uploadcare.com/groups/"

EMPTY_PAGE: Dict[str, Any] = {
    "next": None,
    "previous": None,
    "total": 7,
    "per_page": 100,
    "results": [],
}


def _json_response():
    response = MagicMock()
    response.json.return_value = EMPTY_PAGE
    return response


def _request_url(uploadcare, resource_list):
    with patch.object(
        uploadcare.rest_client, "get", return_value=_json_response()
    ) as mocked_get:
        total = resource_list.count()

    assert total == EMPTY_PAGE["total"]
    mocked_get.assert_called_once()
    return urlparse(mocked_get.call_args.args[0])


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({"stored": True}, {"stored": ["true"]}),
        ({"stored": False}, {"stored": ["false"]}),
        ({"removed": True}, {"removed": ["true"]}),
        (
            {"stored": True, "removed": False},
            {"stored": ["true"], "removed": ["false"]},
        ),
    ],
)
def test_file_count_forwards_filters(uploadcare, kwargs, expected):
    url = _request_url(uploadcare, uploadcare.list_files(**kwargs))

    assert f"{url.scheme}://{url.netloc}{url.path}" == FILES_URL
    assert parse_qs(url.query) == expected


def test_file_count_without_filters_sends_no_query(uploadcare):
    url = _request_url(uploadcare, uploadcare.list_files())

    assert url.query == ""


def test_file_count_does_not_send_limit(uploadcare):
    url = _request_url(uploadcare, uploadcare.list_files(stored=True, limit=5))

    assert parse_qs(url.query) == {"stored": ["true"]}


def test_group_count_sends_no_query(uploadcare):
    url = _request_url(uploadcare, uploadcare.list_file_groups())

    assert f"{url.scheme}://{url.netloc}{url.path}" == GROUPS_URL
    assert url.query == ""
