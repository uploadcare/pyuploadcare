# coding: utf-8
from __future__ import unicode_literals

import random
import re
import time
from pathlib import Path
from tempfile import NamedTemporaryFile


ASSETS_PATH = Path(__file__).parent / "assets"
IMAGE_PATH = ASSETS_PATH / "img.png"

# A freshly uploaded file takes about ten seconds to become searchable.
SEARCH_INDEXING_TIMEOUT = 90
SEARCH_INDEXING_INTERVAL = 2

# Tags allow Latin letters, digits, `-`, `_` and `.` only.
TERM_PATTERN = re.compile(r"[A-Za-z0-9]{4,}")


def upload_image_file(uploadcare, tags=None):
    """Upload the test image, optionally with tags.

    Not stored, so the project's autostore setting cannot leave it behind.
    """
    with open(IMAGE_PATH, "rb") as fh:
        return uploadcare.upload(fh, store=False, tags=tags)


def unique_tag(prefix="pyuploadcare-test"):
    """A tag no other test run will collide on."""
    return f"{prefix}-{random.randint(10 ** 9, 10 ** 10)}"


def search_term(filename):
    """A term from `filename` long enough for a full text condition.

    ``query`` and ``phrase`` values must be at least 4 characters, so a
    filename without such a run cannot be searched for. Returns ``None`` then.
    """
    match = TERM_PATTERN.search(filename or "")
    return match.group(0) if match else None


def wait_until_searchable(
    uploadcare,
    request,
    limit=5,
    timeout=SEARCH_INDEXING_TIMEOUT,
    interval=SEARCH_INDEXING_INTERVAL,
):
    """Poll search until `request` returns results, then return the response.

    Search indexing is asynchronous, so a file is not findable the moment it
    is uploaded.
    """
    deadline = time.monotonic() + timeout

    while True:
        response = uploadcare.search_files(request, limit=limit)

        if response.results:
            return response

        if time.monotonic() >= deadline:
            raise AssertionError(
                f"search returned nothing within {timeout}s for {request!r}"
            )

        time.sleep(interval)


def upload_tmp_txt_file(uploadcare, content=""):
    tmp_txt_file = NamedTemporaryFile(mode="wb", delete=False)
    tmp_txt_file.write(content.encode("utf-8"))
    tmp_txt_file.close()

    with open(tmp_txt_file.name, "rb") as fh:
        file_ = uploadcare.upload(fh, store=False)
    return file_


def create_file_group(uploadcare, files_qty=1):
    files = [upload_tmp_txt_file(uploadcare) for file_ in range(files_qty)]
    group = uploadcare.create_file_group(files)
    return group
