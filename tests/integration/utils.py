# coding: utf-8
from __future__ import unicode_literals

from tempfile import NamedTemporaryFile

from pyuploadcare import File, FileGroup


def upload_tmp_txt_file(content=""):
    tmp_txt_file = NamedTemporaryFile(mode="wb", delete=False)
    tmp_txt_file.write(content.encode("utf-8"))
    tmp_txt_file.close()

    with open(tmp_txt_file.name, "rb") as fh:
        file_ = File.upload(fh, store=False)
    return file_


def create_file_group(files_qty=1):
    files = [upload_tmp_txt_file() for file_ in range(files_qty)]
    group = FileGroup.create(files)
    return group
