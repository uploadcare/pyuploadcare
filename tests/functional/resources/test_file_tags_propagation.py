"""``tags`` must reach the Upload API through every public upload wrapper."""

from unittest.mock import patch

import pytest

from pyuploadcare.exceptions import InvalidParamError


TAGS = ["cat", "animal"]
UPLOADED_UUID = "a55d6b25-d03c-4038-9838-6e06bb7df598"


def test_upload_files_forwards_tags(uploadcare, small_file):
    with patch.object(
        uploadcare.upload_api,
        "upload",
        return_value={"sample1.txt": UPLOADED_UUID},
    ) as mocked_upload:
        with open(small_file.name, "rb") as fh:
            uploadcare.upload_files([fh], tags=TAGS)

    assert mocked_upload.call_args.kwargs["tags"] == TAGS


def test_upload_files_omits_tags_when_not_given(uploadcare, small_file):
    with patch.object(
        uploadcare.upload_api,
        "upload",
        return_value={"sample1.txt": UPLOADED_UUID},
    ) as mocked_upload:
        with open(small_file.name, "rb") as fh:
            uploadcare.upload_files([fh])

    assert mocked_upload.call_args.kwargs["tags"] is None


def test_direct_upload_forwards_tags(uploadcare, small_file):
    """Files below ``multipart_min_file_size`` take the direct upload path."""
    with patch.object(
        uploadcare.upload_api,
        "upload",
        return_value={"sample1.txt": UPLOADED_UUID},
    ) as mocked_upload:
        with open(small_file.name, "rb") as fh:
            uploadcare.upload(fh, tags=TAGS)

    assert mocked_upload.call_args.kwargs["tags"] == TAGS


def _patched_multipart(uploadcare):
    """Patch the three Upload API calls a multipart upload makes."""
    return (
        patch.object(
            uploadcare.upload_api,
            "start_multipart_upload",
            return_value={
                "uuid": UPLOADED_UUID,
                "parts": ["https://s3.example/part-1"],
            },
        ),
        patch.object(uploadcare.upload_api, "multipart_upload_chunk"),
        patch.object(
            uploadcare.upload_api,
            "multipart_complete",
            return_value={"uuid": UPLOADED_UUID},
        ),
    )


def test_multipart_upload_forwards_tags(uploadcare, memo_file):
    stream, size = memo_file
    start, chunk, complete = _patched_multipart(uploadcare)

    with start as mocked_start, chunk, complete:
        uploadcare.multipart_upload(stream, size=size, tags=TAGS)

    assert mocked_start.call_args.kwargs["tags"] == TAGS


def test_upload_uses_multipart_path_for_big_files(uploadcare, memo_file):
    """``upload()`` must forward tags on the multipart branch too."""
    stream, size = memo_file
    start, chunk, complete = _patched_multipart(uploadcare)

    with patch.object(uploadcare, "multipart_min_file_size", 1):
        with start as mocked_start, chunk, complete:
            uploadcare.upload(stream, size=size, tags=TAGS)

    assert mocked_start.call_args.kwargs["tags"] == TAGS


def test_upload_from_url_rejects_tags(uploadcare):
    """`/from_url/` does not support tags, so they must not be dropped."""
    with patch.object(uploadcare, "upload_from_url_sync") as mocked_upload:
        with pytest.raises(InvalidParamError):
            uploadcare.upload("https://example.com/file.jpg", tags=TAGS)

    mocked_upload.assert_not_called()


def test_upload_from_url_without_tags_still_works(uploadcare):
    with patch.object(uploadcare, "upload_from_url_sync") as mocked_upload:
        uploadcare.upload("https://example.com/file.jpg")

    mocked_upload.assert_called_once()
