"""Response parsing for ``TagsAPI``.

Request bodies are asserted in ``test_tags_api_requests.py`` instead: VCR
matches on method and URI only.
"""

import pytest

from pyuploadcare.api.responses import UpdateFileTagsResponse


FILE_UUID = "a55d6b25-d03c-4038-9838-6e06bb7df598"


@pytest.mark.vcr
def test_get_file_tags(uploadcare):
    assert uploadcare.tags_api.get(FILE_UUID) == ["cat", "animal"]


@pytest.mark.vcr
def test_get_empty_file_tags(uploadcare):
    tags = uploadcare.tags_api.get("1a9c5240-7d9b-4473-851b-45fa4b0bed64")
    assert tags == []


@pytest.mark.vcr
def test_replace_file_tags(uploadcare):
    response = uploadcare.tags_api.replace(
        FILE_UUID, ["cat", "animal", "cute"]
    )

    assert isinstance(response, UpdateFileTagsResponse)
    assert response.tags == ["cat", "animal", "cute"]
    assert response.added == ["animal", "cute"]
    assert response.deleted == ["dog"]


@pytest.mark.vcr
def test_update_file_tags(uploadcare):
    response = uploadcare.tags_api.update(
        FILE_UUID, add=["cat"], delete=["dog"]
    )

    assert isinstance(response, UpdateFileTagsResponse)
    assert response.tags == ["pet", "cat"]
    assert response.added == ["cat"]
    assert response.deleted == ["dog"]
