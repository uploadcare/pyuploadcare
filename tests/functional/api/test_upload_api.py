from unittest.mock import ANY

import pytest

from pyuploadcare import api


@pytest.mark.vcr
def test_upload_file(small_file):
    upload_api = api.UploadAPI()
    filename = "file.txt"
    with open(small_file.name, "rb") as fh:
        response = upload_api.upload({filename: fh})
    assert response == {filename: ANY}


@pytest.mark.vcr
def test_upload_file_secure(small_file):
    upload_api = api.UploadAPI()
    filename = "file.txt"
    with open(small_file.name, "rb") as fh:
        response = upload_api.upload(
            {filename: fh},
            secure_upload=True,
        )

    assert response == {filename: ANY}


@pytest.mark.vcr
def test_multipart_upload(big_file):
    upload_api = api.UploadAPI()
    filename = "file.txt"
    chunk_size = 5 * 1024 * 1024

    chunks = []
    with open(big_file.name, "rb") as fh:
        chunk = fh.read(chunk_size)
        while chunk:
            chunks.append(chunk)
            chunk = fh.read(chunk_size)

    size = sum(map(len, chunks))

    content_type = "text/plain"

    response = upload_api.start_multipart_upload(filename, size, content_type)

    assert response == {"uuid": ANY, "parts": [ANY, ANY, ANY]}
    multipart_uuid = response["uuid"]

    for chunk_url, chunk in zip(response["parts"], chunks):
        upload_api.multipart_upload_chunk(chunk_url, chunk)

    response = upload_api.multipart_complete(multipart_uuid)
    assert "file_id" in response
