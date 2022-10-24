import os
from tempfile import TemporaryDirectory

import pytest

from pyuploadcare import conf
from pyuploadcare.client import Uploadcare


@pytest.fixture()
def temp_directory():
    return TemporaryDirectory()


@pytest.fixture()
def small_file(temp_directory):
    path = os.path.join(temp_directory.name, "sample1.txt")
    with open(path, "w") as fh:
        fh.write("test1")
    return fh


@pytest.fixture()
def small_file2(temp_directory):
    path = os.path.join(temp_directory.name, "sample2.txt")
    with open(path, "w") as fh:
        fh.write("test2")
    return fh


@pytest.fixture()
def big_file(temp_directory):
    path = os.path.join(temp_directory.name, "big_file.txt")
    with open(path, "wb") as fh:
        fh.write(b"0" * 11_000_000)
    return fh


@pytest.fixture(autouse=True)
def setup_settings():
    conf.pub_key = "demopublickey"
    conf.secret = "demosecretkey"
    conf.api_version = "0.7"
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


@pytest.fixture(scope="module")
def uploadcare():
    return Uploadcare(
        public_key="demopublickey",
        secret_key="demosecretkey",
    )
