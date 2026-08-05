import pytest

from pyuploadcare.api.entities import FileInfo


FILE_UUID = "a55d6b25-d03c-4038-9838-6e06bb7df598"

FILE_INFO_WITH_TAGS = {
    "uuid": FILE_UUID,
    "original_filename": "sample.jpg",
    "tags": ["cat", "animal"],
}


def test_file_info_parses_tags():
    file_info = FileInfo.model_validate(FILE_INFO_WITH_TAGS)
    assert file_info.tags == ["cat", "animal"]


def test_file_info_parses_empty_tags():
    file_info = FileInfo.model_validate({"uuid": FILE_UUID, "tags": []})
    assert file_info.tags == []


def test_file_info_without_tags_dumps_none():
    """Endpoints that do not report tags leave the field as ``None``.

    Regression guard: ``model_dump()`` gained a new ``tags`` key, which
    consumers of ``File.info`` will now see.
    """
    file_info = FileInfo.model_validate({"uuid": FILE_UUID})
    assert file_info.tags is None
    assert file_info.model_dump()["tags"] is None


def test_file_tags_property_reads_from_info(uploadcare):
    file_ = uploadcare.file(FILE_UUID, FILE_INFO_WITH_TAGS)
    assert file_.tags == ["cat", "animal"]


@pytest.mark.vcr
def test_file_get_tags(uploadcare):
    file_ = uploadcare.file(FILE_UUID)
    assert file_.get_tags() == ["cat", "animal"]


def test_file_get_tags_refreshes_cached_info(uploadcare, vcr):
    file_ = uploadcare.file(FILE_UUID, {"uuid": FILE_UUID, "tags": []})

    with vcr.use_cassette("test_file_get_tags"):
        assert file_.get_tags() == ["cat", "animal"]

    assert file_.info["tags"] == ["cat", "animal"]


@pytest.mark.vcr
def test_file_set_tags(uploadcare):
    file_ = uploadcare.file(FILE_UUID)
    response = file_.set_tags(["cat", "cute"])

    assert response.tags == ["cat", "cute"]
    assert response.added == ["cute"]
    assert response.deleted == ["animal"]


def test_file_set_tags_refreshes_cached_info(uploadcare, vcr):
    file_ = uploadcare.file(FILE_UUID, dict(FILE_INFO_WITH_TAGS))

    with vcr.use_cassette("test_file_set_tags"):
        file_.set_tags(["cat", "cute"])

    assert file_.info["tags"] == ["cat", "cute"]


@pytest.mark.vcr
def test_file_update_tags(uploadcare):
    file_ = uploadcare.file(FILE_UUID)
    response = file_.update_tags(add=["cute"], delete=["animal"])

    assert response.tags == ["cat", "cute"]
    assert response.added == ["cute"]
    assert response.deleted == ["animal"]


def test_file_update_tags_refreshes_cached_info(uploadcare, vcr):
    file_ = uploadcare.file(FILE_UUID, dict(FILE_INFO_WITH_TAGS))

    with vcr.use_cassette("test_file_update_tags"):
        file_.update_tags(add=["cute"], delete=["animal"])

    assert file_.info["tags"] == ["cat", "cute"]
