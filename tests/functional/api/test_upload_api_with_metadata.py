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
