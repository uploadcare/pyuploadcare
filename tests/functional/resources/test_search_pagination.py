"""Pagination behaviour of ``Uploadcare.iterate_search_files``."""

from unittest.mock import patch
from uuid import UUID

import pytest
from pydantic import ValidationError

from pyuploadcare.api.api import (
    SEARCH_DEFAULT_LIMIT,
    SEARCH_MAX_LIMIT,
    SEARCH_MAX_WINDOW,
)
from pyuploadcare.api.responses import FileSearchResponse
from pyuploadcare.exceptions import InvalidParamError


# Filter-only requests have an undefined order, so every request used for
# paging carries an explicit `sort`. See `test_undefined_order_warning`.
REQUEST = {"tags": {"all": ["cat"]}, "sort": ["-datetime_uploaded"]}

# A `next` URL pointing somewhere else entirely. The iterator must never
# request it: the REST client attaches credentials to any URL it is given.
HOSTILE_NEXT = "https://evil.example/files/search/?limit=2&offset=999"


def _uuid(index: int) -> str:
    return str(UUID(int=index))


def _page(count, next_url=None, total=None, offset=0, per_page=None):
    return FileSearchResponse.model_validate(
        {
            "next": next_url,
            "previous": None,
            "total": count if total is None else total,
            "per_page": count if per_page is None else per_page,
            "results": [
                {"uuid": _uuid(offset + index)} for index in range(count)
            ],
        }
    )


def _patched_search(uploadcare, pages):
    return patch.object(uploadcare.files_api, "search", side_effect=pages)


def _offsets(mocked_search):
    return [call.kwargs["offset"] for call in mocked_search.call_args_list]


def _limits(mocked_search):
    return [call.kwargs["limit"] for call in mocked_search.call_args_list]


def test_single_page_is_yielded(uploadcare):
    with _patched_search(uploadcare, [_page(3)]):
        results = list(uploadcare.iterate_search_files(REQUEST))

    assert len(results) == 3


def test_follows_pages_until_next_is_none(uploadcare):
    pages = [
        _page(2, next_url=HOSTILE_NEXT, total=4),
        _page(2, next_url=None, total=4, offset=2),
    ]

    with _patched_search(uploadcare, pages) as mocked_search:
        results = list(
            uploadcare.iterate_search_files(REQUEST, request_limit=2)
        )

    assert [str(item.uuid) for item in results] == [_uuid(i) for i in range(4)]
    assert _offsets(mocked_search) == [0, 2]


def test_offset_advances_by_the_requested_page_size(uploadcare):
    """Offset pagination advances by the window, not by results received.

    A short page that still reports a `next` would otherwise make the
    following request overlap it and repeat files.
    """
    pages = [
        # Asked for 20, got 3, but there is more.
        _page(3, next_url=HOSTILE_NEXT, total=99, per_page=20),
        _page(0, next_url=None, total=99, per_page=20),
    ]

    with _patched_search(uploadcare, pages) as mocked_search:
        list(uploadcare.iterate_search_files(REQUEST))

    assert _offsets(mocked_search) == [0, SEARCH_DEFAULT_LIMIT]


def test_next_url_is_never_requested(uploadcare):
    """Offsets are computed locally, never taken from the `next` URL."""
    pages = [
        _page(2, next_url=HOSTILE_NEXT, total=4),
        _page(2, next_url=None, total=4, offset=2),
    ]

    with _patched_search(uploadcare, pages) as mocked_search:
        with patch.object(uploadcare.rest_client, "post") as mocked_post:
            list(uploadcare.iterate_search_files(REQUEST, request_limit=2))

    mocked_post.assert_not_called()
    # `HOSTILE_NEXT` advertises offset 999 on another origin; ignored.
    assert _offsets(mocked_search) == [0, 2]


def test_stops_on_an_empty_page(uploadcare):
    pages = [
        _page(2, next_url=HOSTILE_NEXT, total=99),
        _page(0, next_url=HOSTILE_NEXT, total=99),
    ]

    with _patched_search(uploadcare, pages) as mocked_search:
        results = list(
            uploadcare.iterate_search_files(REQUEST, request_limit=2)
        )

    assert len(results) == 2
    assert mocked_search.call_count == 2


def test_does_not_stop_on_an_understated_total(uploadcare):
    """`total` is documented as possibly approximate, so it is not a stop."""
    pages = [
        _page(2, next_url=HOSTILE_NEXT, total=2),
        _page(2, next_url=None, total=2, offset=2),
    ]

    with _patched_search(uploadcare, pages):
        results = list(
            uploadcare.iterate_search_files(REQUEST, request_limit=2)
        )

    assert len(results) == 4


def test_limit_caps_the_total_yielded(uploadcare):
    pages = [_page(2, next_url=HOSTILE_NEXT, total=99)]

    with _patched_search(uploadcare, pages) as mocked_search:
        results = list(uploadcare.iterate_search_files(REQUEST, limit=2))

    assert len(results) == 2
    assert mocked_search.call_count == 1


def test_limit_smaller_than_a_page_truncates_mid_page(uploadcare):
    pages = [_page(5, next_url=HOSTILE_NEXT, total=99)]

    with _patched_search(uploadcare, pages) as mocked_search:
        results = list(uploadcare.iterate_search_files(REQUEST, limit=3))

    assert len(results) == 3
    # The page size is clamped to the remaining amount.
    assert _limits(mocked_search) == [3]


def test_limit_zero_makes_no_request(uploadcare):
    with patch.object(uploadcare.files_api, "search") as mocked_search:
        results = list(uploadcare.iterate_search_files(REQUEST, limit=0))

    assert results == []
    mocked_search.assert_not_called()


def test_default_page_size(uploadcare):
    with _patched_search(uploadcare, [_page(1)]) as mocked_search:
        list(uploadcare.iterate_search_files(REQUEST))

    assert _limits(mocked_search) == [SEARCH_DEFAULT_LIMIT]


def test_request_limit_sets_the_page_size(uploadcare):
    with _patched_search(uploadcare, [_page(1)]) as mocked_search:
        list(uploadcare.iterate_search_files(REQUEST, request_limit=7))

    assert _limits(mocked_search) == [7]


def test_offset_is_forwarded(uploadcare):
    with _patched_search(uploadcare, [_page(1)]) as mocked_search:
        list(uploadcare.iterate_search_files(REQUEST, offset=42))

    assert _offsets(mocked_search) == [42]


@pytest.mark.parametrize(
    "offset, expected_page_size",
    [
        (SEARCH_MAX_WINDOW - 10, 10),
        (SEARCH_MAX_WINDOW - 50, 20),
        (SEARCH_MAX_WINDOW - 1, 1),
    ],
)
def test_page_size_is_clamped_to_the_search_window(
    uploadcare, offset, expected_page_size
):
    """`offset` + `limit` must never exceed the window."""
    with _patched_search(uploadcare, [_page(1, offset=offset)]) as mocked:
        list(uploadcare.iterate_search_files(REQUEST, offset=offset))

    call = mocked.call_args_list[0]
    assert call.kwargs["limit"] == expected_page_size
    assert call.kwargs["offset"] + call.kwargs["limit"] <= SEARCH_MAX_WINDOW


def test_stops_at_the_search_window(uploadcare):
    """Paging cannot go past the first 1000 results."""
    offset = SEARCH_MAX_WINDOW - 2
    pages = [_page(2, next_url=HOSTILE_NEXT, total=99, offset=offset)]

    with _patched_search(uploadcare, pages) as mocked_search:
        results = list(uploadcare.iterate_search_files(REQUEST, offset=offset))

    assert len(results) == 2
    assert mocked_search.call_count == 1


def test_offset_at_the_window_makes_no_request(uploadcare):
    with patch.object(uploadcare.files_api, "search") as mocked_search:
        results = list(
            uploadcare.iterate_search_files(REQUEST, offset=SEARCH_MAX_WINDOW)
        )

    assert results == []
    mocked_search.assert_not_called()


# --- argument and request validation ----------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": -1},
        {"request_limit": 0},
        {"request_limit": -1},
        {"request_limit": SEARCH_MAX_LIMIT + 1},
        {"offset": -1},
        {"offset": SEARCH_MAX_WINDOW + 1},
    ],
)
def test_rejects_out_of_range_arguments(uploadcare, kwargs):
    with patch.object(uploadcare.files_api, "search") as mocked_search:
        with pytest.raises(InvalidParamError):
            uploadcare.iterate_search_files(REQUEST, **kwargs)

    mocked_search.assert_not_called()


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
    with patch.object(uploadcare.files_api, "search") as mocked_search:
        with pytest.raises(InvalidParamError):
            uploadcare.iterate_search_files(REQUEST, **kwargs)

    mocked_search.assert_not_called()


def test_argument_errors_are_raised_eagerly(uploadcare):
    """Not deferred until the returned iterator is first advanced."""
    with pytest.raises(InvalidParamError):
        uploadcare.iterate_search_files(REQUEST, limit=-1)


def test_invalid_request_is_rejected_eagerly(uploadcare):
    """The request itself is validated by the wrapper, not by the generator."""
    with patch.object(uploadcare.files_api, "search") as mocked_search:
        with pytest.raises(ValidationError):
            uploadcare.iterate_search_files({})

    mocked_search.assert_not_called()


def test_invalid_request_is_rejected_even_with_limit_zero(uploadcare):
    """`limit=0` short-circuits paging but must not skip validation."""
    with pytest.raises(ValidationError):
        uploadcare.iterate_search_files({}, limit=0)


def test_request_is_validated_only_once(uploadcare):
    """The generator receives a model, so pages do not re-validate."""
    pages = [
        _page(2, next_url=HOSTILE_NEXT, total=4),
        _page(2, next_url=None, total=4, offset=2),
    ]

    with _patched_search(uploadcare, pages) as mocked_search:
        list(uploadcare.iterate_search_files(REQUEST, request_limit=2))

    requests = [call.args[0] for call in mocked_search.call_args_list]
    assert len(requests) == 2
    assert requests[0] is requests[1]


# --- undefined result order -------------------------------------------------


def test_undefined_order_warning(uploadcare):
    """A filter-only request without `sort` has an undefined order."""
    with _patched_search(uploadcare, [_page(1)]):
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
    import warnings

    with _patched_search(uploadcare, [_page(1)]):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            list(uploadcare.iterate_search_files(request_))
