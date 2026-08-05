# coding: utf-8
from __future__ import unicode_literals

from pathlib import Path
from tempfile import NamedTemporaryFile


ASSETS_PATH = Path(__file__).parent / "assets"
IMAGE_PATH = ASSETS_PATH / "img.png"


def upload_image_file(uploadcare, tags=None):
    """Upload the test image, optionally with tags.

    Not stored, so the project's autostore setting cannot leave it behind.
    """
    with open(IMAGE_PATH, "rb") as fh:
        return uploadcare.upload(fh, store=False, tags=tags)


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
