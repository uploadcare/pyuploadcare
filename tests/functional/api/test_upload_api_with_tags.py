"""Request shape assertions for tags in the Upload API.

Tags are sent as a comma-separated ``tags`` form field, which VCR's default
matcher does not check, so a mocked client is used instead of a cassette.
"""

from unittest.mock import MagicMock, patch

import pytest

from pyuploadcare.exceptions import TagValidationError


def _upload_response(payload=None):
    response = MagicMock()
    response.json.return_value = payload or {}
    return response


@pytest.fixture
def upload_api(uploadcare):
    return uploadcare.upload_api


def _sent_data(mocked_post):
    return mocked_post.call_args.kwargs["data"]


def test_upload_sends_comma_separated_tags(upload_api, small_file):
    with patch.object(
        upload_api._client, "post", return_value=_upload_response()
    ) as mocked_post:
        with open(small_file.name, "rb") as fh:
            upload_api.upload({"file.txt": fh}, tags=["cat", "animal"])

    assert _sent_data(mocked_post)["tags"] == "cat,animal"


def test_upload_normalizes_tags(upload_api, small_file):
    with patch.object(
        upload_api._client, "post", return_value=_upload_response()
    ) as mocked_post:
        with open(small_file.name, "rb") as fh:
            upload_api.upload({"file.txt": fh}, tags=[" Cat ", "CAT", "dog"])

    assert _sent_data(mocked_post)["tags"] == "cat,dog"


def test_upload_omits_tags_when_not_given(upload_api, small_file):
    with patch.object(
        upload_api._client, "post", return_value=_upload_response()
    ) as mocked_post:
        with open(small_file.name, "rb") as fh:
            upload_api.upload({"file.txt": fh})

    assert "tags" not in _sent_data(mocked_post)


@pytest.mark.parametrize("tags", [[], ["", "   "]])
def test_upload_omits_tags_when_they_normalize_to_empty(
    upload_api, small_file, tags
):
    with patch.object(
        upload_api._client, "post", return_value=_upload_response()
    ) as mocked_post:
        with open(small_file.name, "rb") as fh:
            upload_api.upload({"file.txt": fh}, tags=tags)

    assert "tags" not in _sent_data(mocked_post)


def test_upload_rejects_invalid_tags(upload_api, small_file):
    with patch.object(upload_api._client, "post") as mocked_post:
        with open(small_file.name, "rb") as fh:
            with pytest.raises(TagValidationError):
                upload_api.upload({"file.txt": fh}, tags=["not valid"])

    mocked_post.assert_not_called()


def test_start_multipart_upload_sends_comma_separated_tags(upload_api):
    with patch.object(
        upload_api._client,
        "post",
        return_value=_upload_response({"uuid": "x", "parts": []}),
    ) as mocked_post:
        upload_api.start_multipart_upload(
            "file.txt", 100, "text/plain", tags=["cat", "animal"]
        )

    assert _sent_data(mocked_post)["tags"] == "cat,animal"


def test_start_multipart_upload_omits_tags_when_not_given(upload_api):
    with patch.object(
        upload_api._client,
        "post",
        return_value=_upload_response({"uuid": "x", "parts": []}),
    ) as mocked_post:
        upload_api.start_multipart_upload("file.txt", 100, "text/plain")

    assert "tags" not in _sent_data(mocked_post)
