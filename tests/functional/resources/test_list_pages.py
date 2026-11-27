"""Single-page list access: ``list_page`` / ``fetch_page`` and the
``Uploadcare.list_*_page`` / ``fetch_*_page`` wrappers.

Pages are mocked at the HTTP client, so the tests see the URLs requested.
"""

from datetime import datetime, timezone
from typing import cast
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import pytest

from pyuploadcare.api.entities import FileInfo, GroupInfo, Webhook
from pyuploadcare.api.responses import PaginatedResponse
from pyuploadcare.exceptions import InvalidParamError, InvalidRequestError


API_BASE = "https://api.uploadcare.com/"
FILES_URL = f"{API_BASE}files/"
GROUPS_URL = f"{API_BASE}groups/"


def _uuid(index: int) -> str:
    return str(UUID(int=index))


def _page(results, next_url=None, previous=None, total=None, per_page=None):
    return {
        "next": next_url,
        "previous": previous,
        "total": len(results) if total is None else total,
        "per_page": len(results) if per_page is None else per_page,
        "results": results,
    }


def _files(count, offset=0):
    return [{"uuid": _uuid(offset + index)} for index in range(count)]


def _groups(count):
    return [{"id": f"{_uuid(index)}~1", "files_count": 1} for index in range(count)]


def _patched_get(uploadcare, *pages):
    return patch.object(
        uploadcare.rest_client,
        "get",
        side_effect=[Mock(json=Mock(return_value=page)) for page in pages],
    )


def _url(mocked_get, index=-1):
    return mocked_get.call_args_list[index].args[0]


def _path(url):
    split = urlsplit(url)
    return f"{split.scheme}://{split.netloc}{split.path}"


def _query(url):
    return parse_qs(urlsplit(url).query)


# Files


def test_list_files_page_returns_one_page(uploadcare):
    next_url = f"{FILES_URL}?limit=2&from=2026-01-01T00%3A00%3A00"
    page = _page(_files(2), next_url=next_url, total=5, per_page=2)

    with _patched_get(uploadcare, page) as mocked_get:
        response = uploadcare.list_files_page(request_limit=2)

    assert mocked_get.call_count == 1
    assert all(isinstance(item, FileInfo) for item in response.results)
    assert [str(item.uuid) for item in response.results] == [
        _uuid(0),
        _uuid(1),
    ]
    assert response.next == next_url
    assert response.previous is None
    assert response.total == 5
    assert response.per_page == 2
    assert _path(_url(mocked_get)) == FILES_URL
    assert _query(_url(mocked_get)) == {"limit": ["2"]}


def test_list_files_page_passes_filters(uploadcare):
    starting_point = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with _patched_get(uploadcare, _page([])) as mocked_get:
        uploadcare.list_files_page(
            starting_point=starting_point,
            ordering="-datetime_uploaded",
            request_limit=10,
            stored=True,
            removed=False,
        )

    assert _query(_url(mocked_get)) == {
        "from": [starting_point.isoformat()],
        "ordering": ["-datetime_uploaded"],
        "limit": ["10"],
        "stored": ["true"],
        "removed": ["false"],
    }


def test_list_files_page_requires_aware_starting_point(uploadcare):
    with pytest.raises(ValueError, match="timezone-aware"):
        uploadcare.list_files_page(starting_point=datetime(2026, 1, 1))


@pytest.mark.parametrize(
    "next_url",
    [
        f"{FILES_URL}?limit=2&offset=2",
        "/files/?limit=2&offset=2",
        "files/?limit=2&offset=2",
    ],
)
def test_fetch_files_page(uploadcare, next_url):
    page = _page(_files(2, offset=2), previous=FILES_URL, total=4)

    with _patched_get(uploadcare, page) as mocked_get:
        response = uploadcare.fetch_files_page(next_url)

    assert [str(item.uuid) for item in response.results] == [
        _uuid(2),
        _uuid(3),
    ]
    assert response.previous == FILES_URL
    assert _path(_url(mocked_get)) == FILES_URL
    assert _query(_url(mocked_get)) == {"limit": ["2"], "offset": ["2"]}


def test_pages_can_be_walked_with_next(uploadcare):
    first = _page(_files(2), next_url=f"{FILES_URL}?offset=2", total=3)
    second = _page(_files(1, offset=2), total=3)

    with _patched_get(uploadcare, first, second) as mocked_get:
        page = uploadcare.list_files_page(request_limit=2)
        seen = list(page.results)
        while page.next:
            page = uploadcare.fetch_files_page(page.next)
            seen.extend(page.results)

    assert [str(item.uuid) for item in seen] == [_uuid(i) for i in range(3)]
    assert mocked_get.call_count == 2


@pytest.mark.parametrize(
    "next_url",
    [
        "https://evil.example/files/?limit=2",
        "//evil.example/files/?limit=2",
        "http://api.uploadcare.com/files/?limit=2",
        "https://api.uploadcare.com:8443/files/?limit=2",
        "https://api.uploadcare.com.evil.example/files/",
    ],
)
def test_fetch_files_page_refuses_foreign_origin(uploadcare, next_url):
    with _patched_get(uploadcare) as mocked_get:
        with pytest.raises(InvalidRequestError, match="refusing to follow"):
            uploadcare.fetch_files_page(next_url)

    mocked_get.assert_not_called()


@pytest.mark.parametrize("next_url", ["", None, 42])
def test_fetch_files_page_requires_url(uploadcare, next_url):
    with _patched_get(uploadcare) as mocked_get:
        with pytest.raises(InvalidParamError):
            uploadcare.fetch_files_page(next_url)

    mocked_get.assert_not_called()


# Groups


def test_list_file_groups_page(uploadcare):
    starting_point = datetime(2026, 1, 1, tzinfo=timezone.utc)
    next_url = f"{GROUPS_URL}?limit=2&offset=2"
    page = _page(_groups(2), next_url=next_url, total=3, per_page=2)

    with _patched_get(uploadcare, page) as mocked_get:
        response = uploadcare.list_file_groups_page(
            starting_point=starting_point,
            ordering="datetime_created",
            request_limit=2,
        )

    assert all(isinstance(item, GroupInfo) for item in response.results)
    assert response.next == next_url
    assert response.total == 3
    assert _path(_url(mocked_get)) == GROUPS_URL
    assert _query(_url(mocked_get)) == {
        "from": [starting_point.isoformat()],
        "ordering": ["datetime_created"],
        "limit": ["2"],
    }


def test_fetch_file_groups_page(uploadcare):
    with _patched_get(uploadcare, _page(_groups(1))) as mocked_get:
        response = uploadcare.fetch_file_groups_page("/groups/?offset=2")

    assert len(response.results) == 1
    assert _url(mocked_get) == f"{GROUPS_URL}?offset=2"


def test_fetch_file_groups_page_refuses_foreign_origin(uploadcare):
    with _patched_get(uploadcare) as mocked_get:
        with pytest.raises(InvalidRequestError):
            uploadcare.fetch_file_groups_page("https://evil.example/groups/")

    mocked_get.assert_not_called()


# Webhooks: the endpoint is not paginated


def test_webhooks_list_page_is_the_only_page(uploadcare):
    webhooks = [
        {"id": 1, "target_url": "https://example.com/a"},
        {"id": 2, "target_url": "https://example.com/b"},
    ]

    with _patched_get(uploadcare, webhooks):
        response = uploadcare.webhooks_api.list_page()

    assert isinstance(response, PaginatedResponse)
    assert all(isinstance(item, Webhook) for item in response.results)
    assert [cast(Webhook, item).id for item in response.results] == [1, 2]
    assert response.next is None
    assert response.previous is None
    assert response.total == 2
    assert response.per_page == 2
