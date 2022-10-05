import os
from typing import List
from unittest.mock import ANY

import pytest


TEST_METADATA = {"first_key": "first_value", "second_key": "any_others"}


@pytest.mark.vcr
def test_upload_file_secure_with_metadata(small_file, uploadcare):
    filename = "file851.txt"
    with open(small_file.name, "rb") as fh:
        response = uploadcare.upload_api.upload(
            {filename: fh}, secure_upload=True, common_metadata=TEST_METADATA
        )

    assert response == {filename: ANY}


@pytest.mark.vcr
def test_multipart_upload_with_metadata(big_file, uploadcare):
    filename = "file_md_huge.txt"
    chunk_size = 5 * 1024 * 1024

    with open(big_file.name, "rb") as fh:
        size = os.fstat(fh.fileno()).st_size

        content_type = "text/plain"

        response = uploadcare.upload_api.start_multipart_upload(
            filename,
            size,
            content_type,
            metadata=TEST_METADATA,
            store=False,
        )

        assert response == {"uuid": ANY, "parts": [ANY, ANY, ANY]}
        multipart_uuid = response["uuid"]

        parts: List[str] = response["parts"]

        chunk = fh.read(chunk_size)

        while chunk:
            chunk_url = parts.pop(0)
            uploadcare.upload_api.multipart_upload_chunk(chunk_url, chunk)

            chunk = fh.read(chunk_size)

    response = uploadcare.upload_api.multipart_complete(multipart_uuid)

    assert "file_id" in response
