"""Request shape assertions for file search.

VCR matches on method and URI only, so the POST body has to be asserted
against a mocked client instead of a cassette.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from pyuploadcare.api.api import SEARCH_MAX_LIMIT, SEARCH_MAX_WINDOW
from pyuploadcare.api.search_entities import (
    FileSearchRequest,
    SearchExact,
    TagsFilter,
)
from pyuploadcare.exceptions import InvalidParamError


SEARCH_URL = "https://api.uploadcare.com/files/search/"

EMPTY_PAGE: Dict[str, Any] = {
    "next": None,
    "previous": None,
    "total": 0,
    "per_page": 20,
    "results": [],
}


def _json_response(payload=None):
    response = MagicMock()
    response.json.return_value = payload or EMPTY_PAGE
    return response


@pytest.fixture
def files_api(uploadcare):
    return uploadcare.files_api


def test_search_posts_to_the_search_url(files_api):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search(FileSearchRequest(query="sunset"))

    mocked_post.assert_called_once_with(SEARCH_URL, json={"query": "sunset"})


def test_search_sends_limit_and_offset_as_query_parameters(files_api):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search(
            FileSearchRequest(query="sunset"), limit=50, offset=100
        )

    url = mocked_post.call_args.args[0]
    assert url == f"{SEARCH_URL}?limit=50&offset=100"


def test_search_sends_include_appdata(files_api):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search(
            FileSearchRequest(query="sunset"), include_appdata=True
        )

    assert mocked_post.call_args.args[0] == f"{SEARCH_URL}?include=appdata"


def test_search_omits_pagination_parameters_when_not_given(files_api):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search(FileSearchRequest(query="sunset"))

    assert mocked_post.call_args.args[0] == SEARCH_URL


def test_search_accepts_a_dict_request(files_api):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search({"tags": {"all": ["cat", "Cat"]}})

    assert mocked_post.call_args.kwargs["json"] == {"tags": {"all": ["cat"]}}


def test_search_sends_bracketed_metadata_keys(files_api):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search(
            FileSearchRequest(exact=SearchExact(metadata={"color": ["red"]}))
        )

    assert mocked_post.call_args.kwargs["json"] == {
        "exact": {"metadata[color]": ["red"]}
    }


def test_search_sends_tag_filter_wire_names(files_api):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search(
            FileSearchRequest(tags=TagsFilter(any_=["cat"], none_=["dog"]))
        )

    assert mocked_post.call_args.kwargs["json"] == {
        "tags": {"any": ["cat"], "none": ["dog"]}
    }


def test_search_rejects_an_invalid_dict_before_any_request(files_api):
    with patch.object(files_api._client, "post") as mocked_post:
        with pytest.raises(ValidationError):
            files_api.search({})

    mocked_post.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"limit": -1},
        {"limit": SEARCH_MAX_LIMIT + 1},
        {"offset": -1},
        {"offset": SEARCH_MAX_WINDOW, "limit": 1},
        {"offset": SEARCH_MAX_WINDOW - 10},
        {"offset": SEARCH_MAX_WINDOW - 10, "limit": 20},
    ],
)
def test_search_rejects_out_of_range_pagination(files_api, kwargs):
    with patch.object(files_api._client, "post") as mocked_post:
        with pytest.raises(InvalidParamError):
            files_api.search(FileSearchRequest(query="sunset"), **kwargs)

    mocked_post.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 1.5},
        {"limit": True},
        {"limit": "10"},
        {"offset": 1.5},
        {"offset": False},
        {"offset": "0"},
    ],
)
def test_search_rejects_non_integer_pagination(files_api, kwargs):
    """Annotations are not enforced at runtime and `bool` is an `int`."""
    with patch.object(files_api._client, "post") as mocked_post:
        with pytest.raises(InvalidParamError):
            files_api.search(FileSearchRequest(query="sunset"), **kwargs)

    mocked_post.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 1},
        {"limit": SEARCH_MAX_LIMIT},
        {"offset": 0},
        {"offset": SEARCH_MAX_WINDOW - 1, "limit": 1},
        {"offset": SEARCH_MAX_WINDOW - 20},
    ],
)
def test_search_accepts_pagination_at_the_boundaries(files_api, kwargs):
    with patch.object(
        files_api._client, "post", return_value=_json_response()
    ) as mocked_post:
        files_api.search(FileSearchRequest(query="sunset"), **kwargs)

    mocked_post.assert_called_once()
