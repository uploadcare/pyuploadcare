from tempfile import NamedTemporaryFile

import pytest

from pyuploadcare import conf


@pytest.fixture()
def small_file():
    tmp_file = NamedTemporaryFile(mode="wb", delete=False)
    tmp_file.write("test".encode("utf-8"))
    tmp_file.close()
    return tmp_file


@pytest.fixture()
def big_file():
    tmp_file = NamedTemporaryFile(mode="wb", delete=False)
    tmp_file.write(b"1" * 11_000_000)
    tmp_file.close()
    return tmp_file


@pytest.fixture(autouse=True)
def setup_settings():
    conf.pub_key = "demopublickey"
    conf.secret = "demosecretkey"
    conf.api_version = "0.6"
    conf.api_base = "https://api.uploadcare.com/"
    conf.upload_base = "https://upload.uploadcare.com/"


@pytest.fixture
def signed_uploads():
    old_value = conf.signed_uploads

    conf.signed_uploads = True

    yield

    conf.signed_uploads = old_value


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("authorization", "DUMMY")],
    }
