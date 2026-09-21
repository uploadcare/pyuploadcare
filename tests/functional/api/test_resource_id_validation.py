"""Resource id validation in ``API._build_url``.

``_build_url`` joins the resource id with ``urljoin``, so an unchecked value
like ``"//evil.example/x"`` or an absolute URL would replace the configured
API origin on an authenticated request. Every ``API`` subclass declares the
shape of its resource ids via ``resource_id_pattern``; anything else must be
rejected before a request is made.
"""

from unittest.mock import patch
from uuid import UUID

import pytest

from pyuploadcare.exceptions import InvalidParamError


FILE_UUID = "a55d6b25-d03c-4038-9838-6e06bb7df598"
GROUP_ID = f"{FILE_UUID}~12"

INJECTION_IDS = [
    "//evil.example/files/x",
    "https://evil.example/files/x/",
    "../../files",
    "x/../../files",
    "?limit=1",
    "",
]


@pytest.mark.parametrize("resource_id", INJECTION_IDS)
def test_metadata_api_rejects_crafted_ids(uploadcare, resource_id):
    api = uploadcare.metadata_api
    with patch.object(api._client, "get") as mocked_get:
        with pytest.raises(InvalidParamError):
            api.get_all_metadata(resource_id)

    mocked_get.assert_not_called()


@pytest.mark.parametrize("resource_id", INJECTION_IDS)
def test_files_api_retrieve_rejects_crafted_ids(uploadcare, resource_id):
    api = uploadcare.files_api
    with patch.object(api._client, "get") as mocked_get:
        with pytest.raises(InvalidParamError):
            api.retrieve(resource_id)

    mocked_get.assert_not_called()


@pytest.mark.parametrize("resource_id", INJECTION_IDS)
def test_groups_api_retrieve_rejects_crafted_ids(uploadcare, resource_id):
    api = uploadcare.groups_api
    with patch.object(api._client, "get") as mocked_get:
        with pytest.raises(InvalidParamError):
            api.retrieve(resource_id)

    mocked_get.assert_not_called()


def test_files_api_rejects_group_id(uploadcare):
    """A group id is not a file UUID even though it starts with one."""
    api = uploadcare.files_api
    with patch.object(api._client, "get") as mocked_get:
        with pytest.raises(InvalidParamError):
            api.retrieve(GROUP_ID)

    mocked_get.assert_not_called()


def test_files_api_accepts_uuid_shapes(uploadcare):
    api = uploadcare.files_api
    for resource_id in (FILE_UUID, FILE_UUID.upper(), UUID(FILE_UUID)):
        url = api._build_url(resource_id)
        assert url == f"https://api.uploadcare.com/files/{resource_id}/"


def test_groups_api_accepts_group_id(uploadcare):
    api = uploadcare.groups_api
    url = api._build_url(GROUP_ID)
    assert url == f"https://api.uploadcare.com/groups/{GROUP_ID}/"


def test_webhooks_api_accepts_numeric_id_only(uploadcare):
    api = uploadcare.webhooks_api
    assert api._build_url(42) == "https://api.uploadcare.com/webhooks/42/"

    with pytest.raises(InvalidParamError):
        api._build_url(FILE_UUID)
