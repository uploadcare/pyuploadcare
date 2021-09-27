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
    old_pub_key = conf.pub_key
    old_secret_key = conf.secret

    conf.pub_key = "demopublickey"
    conf.secret = "demosecretkey"

    yield

    conf.pub_key = old_pub_key
    conf.secret = old_secret_key


@pytest.fixture
def signed_uploads():
    old_value = conf.signed_uploads

    conf.signed_uploads = True

    yield

    conf.signed_uploads = old_value
