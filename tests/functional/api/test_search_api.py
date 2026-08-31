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


def test_search_files_parses_file_info(uploadcare, vcr):
    with vcr.use_cassette("test_search_files"):
        response = uploadcare.search_files(
            FileSearchRequest(
                query="sunset", tags=TagsFilter(all_=["cat"]), sort=["-score"]
            ),
            limit=2,
        )

    first = response.results[0]

    assert isinstance(first, FileSearchInfo)
    assert str(first.uuid) == "a55d6b25-d03c-4038-9838-6e06bb7df598"
    assert first.original_filename == "sunset-cat.jpg"
    assert first.size == 3518420
    assert first.is_image is True
    assert first.tags == ["cat", "animal"]
    assert first.metadata == {"album": "holiday"}


def test_search_files_parses_highlight(uploadcare, vcr):
    with vcr.use_cassette("test_search_files"):
        response = uploadcare.search_files(
            FileSearchRequest(
                query="sunset", tags=TagsFilter(all_=["cat"]), sort=["-score"]
            ),
            limit=2,
        )

    highlight = response.results[0].highlight

    assert highlight is not None
    assert highlight.original_filename == ["<em>sunset</em>-cat.jpg"]
    # OpenAPI declares `metadata` as an object of plain strings.
    assert highlight.metadata == {"album": "summer <em>sunset</em>"}
    # Absent for fields that did not match a full-text condition.
    assert highlight.detected_mime_type is None


def test_search_files_handles_a_result_without_tags_or_highlight(
    uploadcare, vcr
):
    with vcr.use_cassette("test_search_files"):
        response = uploadcare.search_files(
            FileSearchRequest(
                query="sunset", tags=TagsFilter(all_=["cat"]), sort=["-score"]
            ),
            limit=2,
        )

    second = response.results[1]

    assert second.tags == []
    assert second.datetime_stored is None
    assert second.highlight is not None
    assert second.highlight.metadata is None


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

    appdata = response.results[0].appdata

    assert appdata is not None
    assert appdata.uc_clamav_virus_scan is not None
    assert appdata.uc_clamav_virus_scan.data.infected is False
