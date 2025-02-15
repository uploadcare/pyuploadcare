import os
import sys
from io import BytesIO
from tempfile import TemporaryDirectory
from typing import Tuple

import pytest

from pyuploadcare import conf
from pyuploadcare.client import Uploadcare


# XXX workaround for vcrpy incompability with Python 3.12
# https://github.com/mgorny/vcrpy/commit/5f2623886dda2fd8bb6035370251fe07cec958ca
# Remove this when an updated version of vcrpy is released.
if sys.version_info >= (3, 12):
    from vcr.stubs import (
        HTTPConnection,
        HTTPSConnection,
        VCRHTTPConnection,
        VCRHTTPSConnection,
    )

    VCRHTTPConnection.debuglevel = HTTPConnection.debuglevel
    VCRHTTPConnection._http_vsn = HTTPConnection._http_vsn
    VCRHTTPSConnection.debuglevel = HTTPSConnection.debuglevel
    VCRHTTPSConnection._http_vsn = HTTPSConnection._http_vsn


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


@pytest.fixture(scope="session")
def setup_settings():
    conf.pub_key = os.environ.get("UPLOADCARE_PUBLIC_KEY", "demopublickey")
    conf.secret = os.environ.get("UPLOADCARE_SECRET_KEY", "demosecretkey")
    conf.api_version = "0.7"
    conf.api_base = "https://api.uploadcare.com/"
    conf.upload_base = "https://upload.uploadcare.com/"

    return conf


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
def uploadcare(setup_settings):
    uc = Uploadcare(
        public_key=setup_settings.pub_key,
        secret_key=setup_settings.secret,
        api_version=setup_settings.api_version,
        multipart_min_file_size=setup_settings.multipart_min_file_size,
        multipart_chunk_size=setup_settings.multipart_chunk_size,
    )
    return uc


@pytest.fixture()
def memo_file(temp_directory) -> Tuple[BytesIO, int]:
    ENOUGH_MILLIONS = 1_000
    mem_file = BytesIO(b"0" * ENOUGH_MILLIONS)
    mem_file.size = ENOUGH_MILLIONS  # type: ignore
    mem_file.name = "_mem.exe"  # type: ignore

    return mem_file, ENOUGH_MILLIONS
