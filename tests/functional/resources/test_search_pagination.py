"""Pagination behaviour of ``Uploadcare.iterate_search_files``.

Pages are mocked at the HTTP client, where the paging engine is observable:
it follows the response's ``next`` URL, re-sending the search request as the
``POST`` body of every page.
"""

import warnings
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import pytest
from pydantic import ValidationError

from pyuploadcare.api.api import (
    SEARCH_DEFAULT_LIMIT,
    SEARCH_MAX_LIMIT,
    SEARCH_MAX_WINDOW,
)
from pyuploadcare.exceptions import InvalidParamError, InvalidRequestError


# Filter-only requests have an undefined order, so every request used for
# paging carries an explicit `sort`. See `test_undefined_order_warning`.
REQUEST = {"tags": {"all": ["cat"]}, "sort": ["-datetime_uploaded"]}

SEARCH_URL = "https://api.uploadcare.com/files/search/"

# A `next` URL pointing somewhere else entirely. The iterator must refuse to
# request it: the REST client attaches credentials to any URL it is given.
HOSTILE_NEXT = "https://evil.example/files/search/?limit=2&offset=999"


def _uuid(index: int) -> str:
    return str(UUID(int=index))


def _next_url(limit, offset):
    return f"{SEARCH_URL}?limit={limit}&offset={offset}"


def _page(count, next_url=None, total=None, offset=0, per_page=None):
    return {
        "next": next_url,
        "previous": None,
        "total": count if total is None else total,
        "per_page": count if per_page is None else per_page,
        "results": [{"uuid": _uuid(offset + index)} for index in range(count)],
    }


def _patched_post(uploadcare, pages):
    return patch.object(
        uploadcare.rest_client,
        "post",
        side_effect=[Mock(json=Mock(return_value=page)) for page in pages],
    )


def _urls(mocked_post):
    return [call.args[0] for call in mocked_post.call_args_list]


def _query_params(url, name):
    return [int(value) for value in parse_qs(urlsplit(url).query)[name]]


def _offsets(mocked_post):
    return [_query_params(url, "offset")[0] for url in _urls(mocked_post)]


def _limits(mocked_post):
    return [_query_params(url, "limit")[0] for url in _urls(mocked_post)]


def _bodies(mocked_post):
    return [call.kwargs["json"] for call in mocked_post.call_args_list]


def test_single_page_is_yielded(uploadcare):
    with _patched_post(uploadcare, [_page(3)]):
        results = list(uploadcare.iterate_search_files(REQUEST))

    assert len(results) == 3


def test_follows_next_until_none(uploadcare):
    pages = [
        _page(2, next_url=_next_url(2, 2), total=4),
        _page(2, next_url=None, total=4, offset=2),
    ]

    with _patched_post(uploadcare, pages) as mocked_post:
        results = list(
            uploadcare.iterate_search_files(REQUEST, request_limit=2)
        )

    assert [str(item.uuid) for item in results] == [_uuid(i) for i in range(4)]
    assert _offsets(mocked_post) == [0, 2]


def test_next_url_is_requested_verbatim(uploadcare):
    """The next page is whatever the server says it is."""
    next_url = _next_url(20, 3)
    pages = [
        # Asked for 20, got 3; the server decides where the next page starts.
        _page(3, next_url=next_url, total=99, per_page=20),
        _page(0, next_url=None, total=99, per_page=20),
    ]

    with _patched_post(uploadcare, pages) as mocked_post:
        list(uploadcare.iterate_search_files(REQUEST))

    assert _urls(mocked_post)[1] == next_url


def test_include_appdata_is_reapplied_to_every_page(uploadcare):
    """The server's `next` does not echo `include`, so the engine must."""
    pages = [
        # `next` as the server sends it: no `include` parameter.
        _page(2, next_url=_next_url(2, 2), total=4),
        _page(2, next_url=None, total=4, offset=2),
    ]

    with _patched_post(uploadcare, pages) as mocked_post:
        list(
            uploadcare.iterate_search_files(
                REQUEST, request_limit=2, include_appdata=True
            )
        )

    for url in _urls(mocked_post):
        assert parse_qs(urlsplit(url).query)["include"] == ["appdata"]


@pytest.mark.parametrize(
    "next_url",
    [
        "HTTPS://API.UPLOADCARE.COM/files/search/?limit=2&offset=2",
        "https://api.uploadcare.com:443/files/search/?limit=2&offset=2",
        "/files/search/?limit=2&offset=2",
    ],
    ids=["uppercase", "explicit-default-port", "relative"],
)
def test_equivalent_origin_next_is_followed(uploadcare, next_url):
    """Origin comparison is not textual: case, an explicit default port and
    a relative URL are all the origin of the search endpoint."""
    pages = [
        _page(2, next_url=next_url, total=4),
        _page(2, next_url=None, total=4, offset=2),
    ]

    with _patched_post(uploadcare, pages) as mocked_post:
        results = list(
            uploadcare.iterate_search_files(REQUEST, request_limit=2)
        )

    assert len(results) == 4
    assert mocked_post.call_count == 2


def test_same_host_other_scheme_next_is_refused(uploadcare):
    """A scheme downgrade is a different origin, even on the same host."""
    pages = [
        _page(
            2,
            next_url="http://api.uploadcare.com/files/search/?limit=2&offset=2",
            total=4,
        )
    ]

    with _patched_post(uploadcare, pages):
        iterator = uploadcare.iterate_search_files(REQUEST, request_limit=2)

        with pytest.raises(InvalidRequestError, match="refusing to follow"):
            list(iterator)


def test_foreign_next_is_refused(uploadcare):
    """`next` is only followed within the origin of the search endpoint."""
    pages = [_page(2, next_url=HOSTILE_NEXT, total=4)]

    with _patched_post(uploadcare, pages) as mocked_post:
        iterator = uploadcare.iterate_search_files(REQUEST, request_limit=2)

        with pytest.raises(InvalidRequestError, match="evil.example"):
            list(iterator)

    # The page before the hostile `next` was requested; the hostile URL never.
    assert _urls(mocked_post) == [_next_url(2, 0)]


def test_every_page_resends_the_request_body(uploadcare):
    pages = [
        _page(2, next_url=_next_url(2, 2), total=4),
        _page(2, next_url=None, total=4, offset=2),
    ]

    with _patched_post(uploadcare, pages) as mocked_post:
        list(uploadcare.iterate_search_files(REQUEST, request_limit=2))

    bodies = _bodies(mocked_post)
    assert len(bodies) == 2
    assert bodies[0]["tags"] == {"all": ["cat"]}
    # The body is rendered once and reused, not re-serialized per page.
    assert bodies[0] is bodies[1]


def test_stops_on_an_empty_page(uploadcare):
    pages = [
        _page(2, next_url=_next_url(2, 2), total=99),
        _page(0, next_url=_next_url(2, 4), total=99),
    ]

    with _patched_post(uploadcare, pages) as mocked_post:
        results = list(
            uploadcare.iterate_search_files(REQUEST, request_limit=2)
        )

    assert len(results) == 2
    assert mocked_post.call_count == 2


def test_does_not_stop_on_an_understated_total(uploadcare):
    """`total` is documented as possibly approximate, so it is not a stop."""
    pages = [
        _page(2, next_url=_next_url(2, 2), total=2),
        _page(2, next_url=None, total=2, offset=2),
    ]

    with _patched_post(uploadcare, pages):
        results = list(
            uploadcare.iterate_search_files(REQUEST, request_limit=2)
        )

    assert len(results) == 4


def test_limit_caps_the_total_yielded(uploadcare):
    pages = [_page(2, next_url=_next_url(2, 2), total=99)]

    with _patched_post(uploadcare, pages) as mocked_post:
        results = list(uploadcare.iterate_search_files(REQUEST, limit=2))

    assert len(results) == 2
    assert mocked_post.call_count == 1


def test_limit_smaller_than_a_page_truncates_the_first_request(uploadcare):
    with _patched_post(uploadcare, [_page(3)]) as mocked_post:
        results = list(uploadcare.iterate_search_files(REQUEST, limit=3))

    assert len(results) == 3
    # The first page is clamped to the remaining amount.
    assert _limits(mocked_post) == [3]


def test_limit_zero_makes_no_request(uploadcare):
    with _patched_post(uploadcare, []) as mocked_post:
        results = list(uploadcare.iterate_search_files(REQUEST, limit=0))

    assert results == []
    mocked_post.assert_not_called()


def test_default_page_size(uploadcare):
    with _patched_post(uploadcare, [_page(1)]) as mocked_post:
        list(uploadcare.iterate_search_files(REQUEST))

    assert _limits(mocked_post) == [SEARCH_DEFAULT_LIMIT]


def test_request_limit_sets_the_page_size(uploadcare):
    with _patched_post(uploadcare, [_page(1)]) as mocked_post:
        list(uploadcare.iterate_search_files(REQUEST, request_limit=7))

    assert _limits(mocked_post) == [7]


def test_offset_is_forwarded(uploadcare):
    with _patched_post(uploadcare, [_page(1)]) as mocked_post:
        list(uploadcare.iterate_search_files(REQUEST, offset=42))

    assert _offsets(mocked_post) == [42]


@pytest.mark.parametrize(
    "offset, expected_page_size",
    [
        (SEARCH_MAX_WINDOW - 10, 10),
        (SEARCH_MAX_WINDOW - 50, 20),
        (SEARCH_MAX_WINDOW - 1, 1),
    ],
)
def test_first_page_is_clamped_to_the_search_window(
    uploadcare, offset, expected_page_size
):
    """`offset` + `limit` must never exceed the window.

    Only the first request is built locally; the pages after it come from
    the server's `next`, which stays within the window on its own.
    """
    with _patched_post(uploadcare, [_page(1, offset=offset)]) as mocked_post:
        list(uploadcare.iterate_search_files(REQUEST, offset=offset))

    (url,) = _urls(mocked_post)
    assert _query_params(url, "limit")[0] == expected_page_size
    assert (
        _query_params(url, "offset")[0] + _query_params(url, "limit")[0]
        <= SEARCH_MAX_WINDOW
    )


def test_offset_at_the_window_raises(uploadcare):
    """Consistent with `search_files`, which rejects the same offset."""
    with _patched_post(uploadcare, []) as mocked_post:
        with pytest.raises(InvalidParamError):
            uploadcare.iterate_search_files(REQUEST, offset=SEARCH_MAX_WINDOW)

    mocked_post.assert_not_called()


# --- argument and request validation ----------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": -1},
        {"request_limit": 0},
        {"request_limit": -1},
        {"request_limit": SEARCH_MAX_LIMIT + 1},
        {"offset": -1},
        {"offset": SEARCH_MAX_WINDOW},
        {"offset": SEARCH_MAX_WINDOW + 1},
    ],
)
def test_rejects_out_of_range_arguments(uploadcare, kwargs):
    with _patched_post(uploadcare, []) as mocked_post:
        with pytest.raises(InvalidParamError):
            uploadcare.iterate_search_files(REQUEST, **kwargs)

    mocked_post.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 1.5},
        {"limit": True},
        {"request_limit": "10"},
        {"request_limit": False},
        {"offset": 2.5},
    ],
)
def test_rejects_non_integer_arguments(uploadcare, kwargs):
    with _patched_post(uploadcare, []) as mocked_post:
        with pytest.raises(InvalidParamError):
            uploadcare.iterate_search_files(REQUEST, **kwargs)

    mocked_post.assert_not_called()


def test_argument_errors_are_raised_eagerly(uploadcare):
    """Not deferred until the returned iterator is first advanced."""
    with pytest.raises(InvalidParamError):
        uploadcare.iterate_search_files(REQUEST, limit=-1)


def test_invalid_request_is_rejected_eagerly(uploadcare):
    """The request itself is validated by the wrapper, not by the generator."""
    with _patched_post(uploadcare, []) as mocked_post:
        with pytest.raises(ValidationError):
            uploadcare.iterate_search_files({})

    mocked_post.assert_not_called()


def test_invalid_request_is_rejected_even_with_limit_zero(uploadcare):
    """`limit=0` short-circuits paging but must not skip validation."""
    with pytest.raises(ValidationError):
        uploadcare.iterate_search_files({}, limit=0)


# --- undefined result order -------------------------------------------------


def test_undefined_order_warning(uploadcare):
    """A filter-only request without `sort` has an undefined order."""
    with _patched_post(uploadcare, [_page(1)]):
        with pytest.warns(UserWarning, match="undefined"):
            list(uploadcare.iterate_search_files({"tags": {"all": ["cat"]}}))


@pytest.mark.parametrize(
    "request_",
    [
        {"tags": {"all": ["cat"]}, "sort": ["-datetime_uploaded"]},
        {"query": "sunset"},
        {"phrase": {"original_filename": "sunset"}},
    ],
)
def test_no_warning_when_the_order_is_defined(uploadcare, request_):
    """`sort`, or relevance from `query`/`phrase`, gives a defined order."""
    with _patched_post(uploadcare, [_page(1)]):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            list(uploadcare.iterate_search_files(request_))
