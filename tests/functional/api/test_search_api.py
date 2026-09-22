"""Response parsing for file search.

Request bodies are asserted in ``test_search_api_requests.py`` instead: VCR
matches on method and URI only.
"""

import pytest

from pyuploadcare.api.entities import FileSearchInfo
from pyuploadcare.api.search_entities import FileSearchRequest, TagsFilter


@pytest.mark.vcr
def test_search_files(uploadcare):
    response = uploadcare.search_files(
        FileSearchRequest(
            query="sunset", tags=TagsFilter(all_=["cat"]), sort=["-score"]
        ),
        limit=2,
    )

    assert response.total == 5
    assert response.per_page == 2
    assert response.previous is None
    assert response.next == (
        "https://api.uploadcare.com/files/search/?limit=2&offset=2"
    )
    assert len(response.results) == 2


MAIN_UUID = "cdc00a7a-366f-4e0b-a942-9a7141b4004b"


def _search_all_fixtures(uploadcare, vcr):
    """All five sunset+cat fixtures on one page.

    Every fixture filename matches ``sunset`` equally well, so the
    relevance order is arbitrary — tests locate results by identity
    instead of rank.
    """
    with vcr.use_cassette("test_search_files_all"):
        return uploadcare.search_files(
            FileSearchRequest(
                query="sunset", tags=TagsFilter(all_=["cat"]), sort=["-score"]
            ),
            limit=5,
        )


def test_search_files_parses_file_info(uploadcare, vcr):
    response = _search_all_fixtures(uploadcare, vcr)

    main = next(
        result for result in response.results if str(result.uuid) == MAIN_UUID
    )

    assert isinstance(main, FileSearchInfo)
    assert main.original_filename == "sunset-cat.jpg"
    assert main.size is not None and main.size > 0
    assert main.is_image is True
    assert sorted(main.tags or []) == ["animal", "cat"]
    assert main.metadata == {"album": "summer sunset"}


def test_search_files_parses_highlight(uploadcare, vcr):
    response = _search_all_fixtures(uploadcare, vcr)

    main = next(
        result for result in response.results if str(result.uuid) == MAIN_UUID
    )
    highlight = main.highlight

    assert highlight is not None
    assert highlight.original_filename == ["<em>sunset</em>-cat.jpg"]
    # OpenAPI declares `metadata` as an object of plain strings.
    assert highlight.metadata == {"album": "summer <em>sunset</em>"}
    # Absent for fields that did not match a full-text condition.
    assert highlight.detected_mime_type is None


def test_search_files_handles_a_result_without_metadata(uploadcare, vcr):
    response = _search_all_fixtures(uploadcare, vcr)

    # The one fixture uploaded with `store=False` and no metadata.
    beach = next(
        result
        for result in response.results
        if result.original_filename == "sunset-beach.jpg"
    )

    assert beach.tags == ["cat"]
    assert beach.datetime_stored is None
    assert beach.highlight is not None
    assert beach.highlight.metadata is None


@pytest.mark.vcr
def test_search_files_empty_result(uploadcare):
    response = uploadcare.search_files(
        FileSearchRequest(query="nothing-matches-this")
    )

    assert response.total == 0
    assert response.results == []
    assert response.next is None


@pytest.mark.vcr
def test_search_files_with_appdata(uploadcare):
    response = uploadcare.search_files(
        FileSearchRequest(tags=TagsFilter(all_=["cat"])),
        include_appdata=True,
    )

    # A filter-only search has an undefined order and the unstored fixture
    # carries no scan, so locate the ClamAV-scanned main fixture directly.
    main = next(
        result for result in response.results if str(result.uuid) == MAIN_UUID
    )
    appdata = main.appdata

    assert appdata is not None
    assert appdata.uc_clamav_virus_scan is not None
    assert appdata.uc_clamav_virus_scan.data.infected is False
