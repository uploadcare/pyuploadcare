# coding: utf-8
from __future__ import unicode_literals

import os
import unittest
from tempfile import NamedTemporaryFile

from pyuploadcare import File, FileGroup


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


# travis-ci.org runs our tests in an overworked virtual machine, which makes
# timing-related tests unreliable.
skip_on_travis = unittest.skipIf(
    "TRAVIS" in os.environ, "timing tests unreliable on travis"
)
