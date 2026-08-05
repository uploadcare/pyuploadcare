"""Request shape assertions for ``TagsAPI``.

VCR matches on method and URI only, so the request body has to be asserted
against a mocked client instead of a cassette.
"""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from pyuploadcare.api.tags import MAX_TAGS_PER_FILE
from pyuploadcare.exceptions import InvalidParamError, TagValidationError


FILE_UUID = "a55d6b25-d03c-4038-9838-6e06bb7df598"
TAGS_URL = f"https://api.uploadcare.com/files/{FILE_UUID}/tags/"


def _json_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


@pytest.fixture
def tags_api(uploadcare):
    return uploadcare.tags_api


def test_get_requests_tags_url(tags_api):
    with patch.object(
        tags_api._client,
        "get",
        return_value=_json_response({"tags": ["cat", "animal"]}),
    ) as mocked_get:
        assert tags_api.get(FILE_UUID) == ["cat", "animal"]

    mocked_get.assert_called_once_with(TAGS_URL)


def test_get_accepts_uuid_instance(tags_api):
    with patch.object(
        tags_api._client, "get", return_value=_json_response({"tags": []})
    ) as mocked_get:
        assert tags_api.get(UUID(FILE_UUID)) == []

    mocked_get.assert_called_once_with(TAGS_URL)


def test_replace_sends_normalized_tags(tags_api):
    payload = {"tags": ["cat", "animal"], "added": ["animal"], "deleted": []}

    with patch.object(
        tags_api._client, "put", return_value=_json_response(payload)
    ) as mocked_put:
        response = tags_api.replace(FILE_UUID, [" Cat ", "ANIMAL", "cat"])

    mocked_put.assert_called_once_with(
        TAGS_URL, json={"tags": ["cat", "animal"]}
    )
    assert response.tags == ["cat", "animal"]
    assert response.added == ["animal"]
    assert response.deleted == []


def test_replace_with_empty_list_clears_tags(tags_api):
    payload = {"tags": [], "added": [], "deleted": ["cat"]}

    with patch.object(
        tags_api._client, "put", return_value=_json_response(payload)
    ) as mocked_put:
        response = tags_api.replace(FILE_UUID, [])

    mocked_put.assert_called_once_with(TAGS_URL, json={"tags": []})
    assert response.deleted == ["cat"]


def test_update_sends_add_and_delete(tags_api):
    payload = {"tags": ["cat"], "added": ["cat"], "deleted": ["dog"]}

    with patch.object(
        tags_api._client, "patch", return_value=_json_response(payload)
    ) as mocked_patch:
        response = tags_api.update(FILE_UUID, add=["Cat"], delete=["dog"])

    mocked_patch.assert_called_once_with(
        TAGS_URL, json={"add": ["cat"], "delete": ["dog"]}
    )
    assert response.added == ["cat"]


def test_update_omits_delete_when_not_given(tags_api):
    payload = {"tags": ["cat"], "added": ["cat"], "deleted": []}

    with patch.object(
        tags_api._client, "patch", return_value=_json_response(payload)
    ) as mocked_patch:
        tags_api.update(FILE_UUID, add=["cat"])

    mocked_patch.assert_called_once_with(TAGS_URL, json={"add": ["cat"]})


def test_update_omits_add_when_not_given(tags_api):
    payload = {"tags": [], "added": [], "deleted": ["cat"]}

    with patch.object(
        tags_api._client, "patch", return_value=_json_response(payload)
    ) as mocked_patch:
        tags_api.update(FILE_UUID, delete=["cat"])

    mocked_patch.assert_called_once_with(TAGS_URL, json={"delete": ["cat"]})


def test_update_allows_more_delete_candidates_than_the_storage_limit(
    tags_api,
):
    """`delete` lists candidates; absent tags are ignored server-side.

    So it may legitimately be longer than the 50-tags-per-file limit.
    """
    delete = [f"tag{index}" for index in range(MAX_TAGS_PER_FILE + 1)]
    payload = {"tags": [], "added": [], "deleted": delete}

    with patch.object(
        tags_api._client, "patch", return_value=_json_response(payload)
    ) as mocked_patch:
        tags_api.update(FILE_UUID, delete=delete)

    mocked_patch.assert_called_once_with(TAGS_URL, json={"delete": delete})


def test_replace_still_enforces_the_storage_limit(tags_api):
    tags = [f"tag{index}" for index in range(MAX_TAGS_PER_FILE + 1)]

    with patch.object(tags_api._client, "put") as mocked_put:
        with pytest.raises(TagValidationError):
            tags_api.replace(FILE_UUID, tags)

    mocked_put.assert_not_called()


def test_update_still_enforces_the_storage_limit_for_add(tags_api):
    """An `add` list longer than the limit can never succeed."""
    add = [f"tag{index}" for index in range(MAX_TAGS_PER_FILE + 1)]

    with patch.object(tags_api._client, "patch") as mocked_patch:
        with pytest.raises(TagValidationError):
            tags_api.update(FILE_UUID, add=add)

    mocked_patch.assert_not_called()


def test_update_without_arguments_sends_empty_body(tags_api):
    """The endpoint documents both fields as optional, so `{}` is valid."""
    payload = {"tags": ["cat"], "added": [], "deleted": []}

    with patch.object(
        tags_api._client, "patch", return_value=_json_response(payload)
    ) as mocked_patch:
        response = tags_api.update(FILE_UUID)

    mocked_patch.assert_called_once_with(TAGS_URL, json={})
    assert response.tags == ["cat"]


@pytest.mark.parametrize(
    "file_uuid",
    [
        "not-a-uuid",
        "//evil.example/files/x",
        "https://evil.example/files/x/",
        "../../files",
        "",
        None,
        42,
    ],
)
def test_invalid_uuid_is_rejected_before_any_request(tags_api, file_uuid):
    """`_build_url` uses `urljoin`, so a crafted id could change the origin."""
    with patch.object(tags_api._client, "get") as mocked_get:
        with pytest.raises(InvalidParamError):
            tags_api.get(file_uuid)

    mocked_get.assert_not_called()


def test_invalid_tags_are_rejected_before_any_request(tags_api):
    with patch.object(tags_api._client, "put") as mocked_put:
        with pytest.raises(TagValidationError):
            tags_api.replace(FILE_UUID, ["not valid"])

    mocked_put.assert_not_called()
