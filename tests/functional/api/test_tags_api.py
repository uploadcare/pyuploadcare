"""Response parsing for ``TagsAPI``.

Request bodies are asserted in ``test_tags_api_requests.py`` instead: VCR
matches on method and URI only.

The cassettes are recorded against the live fixture file (see
``scripts/prepare_vcr_fixtures.py``), whose tags start at the
``["cat", "animal"]`` baseline. The mutating tests run in definition order
and each expectation follows from the state the previous test left behind,
so re-record this module in one piece, after a fixture-script run.
"""

import pytest

from pyuploadcare.api.responses import UpdateFileTagsResponse


FILE_UUID = "cdc00a7a-366f-4e0b-a942-9a7141b4004b"


@pytest.mark.vcr
def test_get_file_tags(uploadcare):
    assert uploadcare.tags_api.get(FILE_UUID) == ["cat", "animal"]


@pytest.mark.vcr
def test_get_empty_file_tags(uploadcare):
    tags = uploadcare.tags_api.get("41a56ce7-48a4-486e-b8ed-4fd5f4051e08")
    assert tags == []


@pytest.mark.vcr
def test_replace_file_tags(uploadcare):
    # State before: ["cat", "animal"] (the baseline).
    response = uploadcare.tags_api.set(FILE_UUID, ["cat", "animal", "cute"])

    assert isinstance(response, UpdateFileTagsResponse)
    assert sorted(response.tags) == ["animal", "cat", "cute"]
    assert response.added == ["cute"]
    assert response.deleted == []


@pytest.mark.vcr
def test_update_file_tags(uploadcare):
    # State before: ["cat", "animal", "cute"], left by the previous test.
    response = uploadcare.tags_api.update(
        FILE_UUID, add=["dog"], delete=["animal"]
    )

    assert isinstance(response, UpdateFileTagsResponse)
    assert sorted(response.tags) == ["cat", "cute", "dog"]
    assert response.added == ["dog"]
    assert response.deleted == ["animal"]
