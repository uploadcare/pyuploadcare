"""File tags against the live REST API.

https://uploadcare.com/docs/file-tags/
"""

import pytest

from pyuploadcare.exceptions import TagValidationError

from .utils import upload_image_file


@pytest.fixture
def tagged_file(uploadcare):
    """A freshly uploaded file carrying tags that need normalizing."""
    file_ = upload_image_file(uploadcare, tags=[" Cat ", "CAT", "animal"])
    yield file_
    file_.delete()


@pytest.fixture
def untagged_file(uploadcare):
    file_ = upload_image_file(uploadcare)
    yield file_
    file_.delete()


def test_upload_attaches_tags(uploadcare, tagged_file):
    """Tags sent as a form field on upload are stored, normalized."""
    assert uploadcare.tags_api.get(tagged_file.uuid) == ["cat", "animal"]


def test_upload_without_tags_stores_none(uploadcare, untagged_file):
    assert uploadcare.tags_api.get(untagged_file.uuid) == []


def test_file_info_reports_tags(tagged_file):
    tagged_file.update_info()
    assert tagged_file.info["tags"] == ["cat", "animal"]


def test_file_info_reports_an_empty_list_without_tags(untagged_file):
    untagged_file.update_info()
    assert untagged_file.info["tags"] == []


def test_list_files_reports_tags(uploadcare, tagged_file):
    """`GET /files/` includes the field, not just `GET /files/{uuid}/`."""
    for file_ in uploadcare.list_files(limit=3, removed=False):
        assert isinstance(file_.info["tags"], list)


def test_get_tags(tagged_file):
    assert tagged_file.get_tags() == ["cat", "animal"]


def test_tags_property_after_direct_upload_loads_the_info(tagged_file):
    """Regression: a direct upload caches nothing, so `tags` fetches it.

    The upload response carries no tags, but the direct upload path leaves
    the info cache unset, so reading the property loads the stored tags.
    """
    assert tagged_file._info_cache is None
    assert tagged_file.tags == ["cat", "animal"]


def test_set_tags(tagged_file):
    response = tagged_file.set_tags(["cat", "cute", "pet"])

    assert response.tags == ["cat", "cute", "pet"]
    assert sorted(response.added) == ["cute", "pet"]
    assert response.deleted == ["animal"]
    assert tagged_file.tags == ["cat", "cute", "pet"]


def test_set_tags_with_an_empty_list_clears_them(uploadcare, tagged_file):
    response = tagged_file.set_tags([])

    assert response.tags == []
    assert sorted(response.deleted) == ["animal", "cat"]
    assert uploadcare.tags_api.get(tagged_file.uuid) == []


def test_update_tags(tagged_file):
    response = tagged_file.update_tags(add=["cute"], delete=["animal"])

    assert response.added == ["cute"]
    assert response.deleted == ["animal"]
    assert sorted(response.tags) == ["cat", "cute"]


def test_update_tags_ignores_absent_deletions(tagged_file):
    """Deleting a tag the file does not have is not an error."""
    response = tagged_file.update_tags(delete=["never-was-there"])

    assert response.deleted == []
    assert response.tags == ["cat", "animal"]


def test_update_tags_skips_already_present_additions(tagged_file):
    response = tagged_file.update_tags(add=["cat"])

    assert response.added == []
    assert response.tags == ["cat", "animal"]


def test_update_tags_without_arguments_returns_the_current_state(
    uploadcare, tagged_file
):
    """The endpoint documents both fields as optional, so `{}` is valid."""
    response = uploadcare.tags_api.update(tagged_file.uuid)

    assert response.tags == ["cat", "animal"]
    assert response.added == []
    assert response.deleted == []


def test_invalid_tags_are_rejected_locally(uploadcare, untagged_file):
    """Validation happens before the request, so the API never sees these."""
    with pytest.raises(TagValidationError):
        uploadcare.tags_api.set(untagged_file.uuid, ["not valid"])
