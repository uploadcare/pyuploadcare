"""File search against the live REST API.

https://uploadcare.com/docs/file-search/

Search indexing is asynchronous, so tests that need to find a file they just
uploaded poll through ``wait_until_searchable``. Everything that only needs
*some* indexed content searches over what the project already holds.
"""

import pytest

from pyuploadcare.api.entities import FileSearchInfo
from pyuploadcare.api.search_entities import (
    FileSearchRequest,
    SearchExact,
    SearchPhrase,
    SizeRange,
    TagsFilter,
)

from .utils import (
    search_term,
    unique_tag,
    upload_image_file,
    wait_until_searchable,
)


# Filter-only requests have an undefined order, so anything paginated or
# order-sensitive carries an explicit sort.
BY_NEWEST = ["-datetime_uploaded"]


@pytest.fixture(scope="module")
def indexed_file(uploadcare):
    """A file already in the project, and therefore already searchable."""
    files = list(uploadcare.list_files(limit=1, removed=False))

    if not files:
        pytest.skip("the project has no files to search")

    return files[0]


@pytest.fixture(scope="module")
def indexed_term(indexed_file):
    term = search_term(indexed_file.info.get("original_filename"))

    if not term:
        pytest.skip("no filename with a 4+ character term to search for")

    return term


def test_search_response_shape(uploadcare):
    """The envelope and every result parse into the SDK's models."""
    response = uploadcare.search_files(
        FileSearchRequest(is_image=True, sort=BY_NEWEST), limit=3
    )

    assert isinstance(response.total, int)
    assert response.per_page == 3
    assert len(response.results) <= 3

    for result in response.results:
        assert isinstance(result, FileSearchInfo)
        assert isinstance(result.tags, list)
        assert result.uuid is not None


def test_query_returns_a_highlight(uploadcare, indexed_term):
    response = uploadcare.search_files(
        FileSearchRequest(query=indexed_term), limit=3
    )

    assert response.total >= 1

    highlighted = [
        value
        for result in response.results
        if result.highlight and result.highlight.original_filename
        for value in result.highlight.original_filename
    ]

    assert highlighted, "expected a highlight for a full text match"
    assert any("<em>" in value for value in highlighted)


def test_phrase_on_original_filename(uploadcare, indexed_term):
    response = uploadcare.search_files(
        FileSearchRequest(phrase=SearchPhrase(original_filename=indexed_term)),
        limit=3,
    )

    assert response.total >= 1


def test_filter_only_search_highlights_nothing(uploadcare):
    """No highlight field is populated without a full text condition.

    The API reference says `highlight` is "absent for filter-only matches",
    but the live API sends an empty object instead, so the model parses it
    into a `SearchHighlight` whose every field is `None`. Either shape is
    handled; what matters is that no field carries a value.
    """
    response = uploadcare.search_files(
        FileSearchRequest(is_image=True, sort=BY_NEWEST), limit=3
    )

    if not response.results:
        pytest.skip("the project has no images to search")

    for result in response.results:
        if result.highlight is None:
            continue

        assert result.highlight.original_filename is None
        assert result.highlight.detected_mime_type is None
        assert result.highlight.metadata is None


def test_exact_uuid(uploadcare, indexed_file):
    response = uploadcare.search_files(
        FileSearchRequest(exact=SearchExact(uuid=[indexed_file.uuid]))
    )

    assert response.total == 1
    assert str(response.results[0].uuid) == indexed_file.uuid


def test_tags_filter_finds_a_tagged_file(uploadcare):
    """Tags attached on upload become searchable once indexed."""
    tag = unique_tag()
    file_ = upload_image_file(uploadcare, tags=[tag])

    try:
        response = wait_until_searchable(
            uploadcare,
            FileSearchRequest(tags=TagsFilter(all_=[tag]), sort=BY_NEWEST),
        )

        assert response.total == 1

        result = response.results[0]
        assert str(result.uuid) == file_.uuid
        assert result.tags == [tag]
    finally:
        file_.delete()


def test_tags_none_filter_excludes_a_tagged_file(uploadcare):
    tag = unique_tag()
    file_ = upload_image_file(uploadcare, tags=[tag])

    try:
        wait_until_searchable(
            uploadcare,
            FileSearchRequest(tags=TagsFilter(all_=[tag]), sort=BY_NEWEST),
        )

        response = uploadcare.search_files(
            FileSearchRequest(tags=TagsFilter(none_=[tag]), sort=BY_NEWEST),
            limit=5,
        )

        found = {str(result.uuid) for result in response.results}
        assert file_.uuid not in found
    finally:
        file_.delete()


def test_size_range(uploadcare):
    response = uploadcare.search_files(
        FileSearchRequest(size=SizeRange(gt=1), sort=BY_NEWEST), limit=3
    )

    assert all(result.size > 1 for result in response.results)


def test_sort_descending_by_size(uploadcare):
    response = uploadcare.search_files(
        FileSearchRequest(is_image=True, sort=["-size"]), limit=5
    )

    sizes = [result.size for result in response.results]
    assert sizes == sorted(sizes, reverse=True)


def test_include_appdata(uploadcare):
    response = uploadcare.search_files(
        FileSearchRequest(is_image=True, sort=BY_NEWEST),
        limit=1,
        include_appdata=True,
    )

    if not response.results:
        pytest.skip("the project has no images to search")

    assert response.results[0].appdata is not None


def test_appdata_is_absent_without_the_flag(uploadcare):
    response = uploadcare.search_files(
        FileSearchRequest(is_image=True, sort=BY_NEWEST), limit=1
    )

    if not response.results:
        pytest.skip("the project has no images to search")

    assert response.results[0].appdata is None


def test_pagination_yields_no_duplicates(uploadcare):
    """Each page is requested at a locally computed offset."""
    uuids = [
        str(result.uuid)
        for result in uploadcare.iterate_search_files(
            FileSearchRequest(is_image=True, sort=BY_NEWEST),
            limit=5,
            request_limit=2,
        )
    ]

    assert len(uuids) <= 5
    assert len(uuids) == len(set(uuids))


def test_pagination_matches_a_single_page(uploadcare):
    request = FileSearchRequest(is_image=True, sort=BY_NEWEST)

    page = uploadcare.search_files(request, limit=4)
    iterated = list(
        uploadcare.iterate_search_files(request, limit=4, request_limit=2)
    )

    assert [str(result.uuid) for result in iterated] == [
        str(result.uuid) for result in page.results
    ]


def test_dict_request(uploadcare):
    """A plain dict in the SDK's shape works like the model."""
    response = uploadcare.search_files(
        {"is_image": True, "sort": ["-datetime_uploaded"]}, limit=1
    )

    assert isinstance(response.total, int)
