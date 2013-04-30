# coding: utf-8
from __future__ import unicode_literals
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from tempfile import NamedTemporaryFile

from pyuploadcare import conf
from pyuploadcare.api_resources import File, FileGroup


def upload_tmp_txt_file(content=''):
    conf.pub_key = 'demopublickey'

    tmp_config_file = NamedTemporaryFile(mode='w+t', delete=False)
    tmp_config_file.write(content)
    tmp_config_file.close()

    with open(tmp_config_file.name) as fh:
        file_ = File.upload(fh)
    return file_


def create_file_group(files_qty=1):
    files = [upload_tmp_txt_file() for file_ in range(files_qty)]
    group = FileGroup.create(files)
    return group


# travis-ci.org runs our tests in an overworked virtual machine, which makes
# timing-related tests unreliable.
skip_on_travis = unittest.skipIf('TRAVIS' in os.environ,
                                 'timing tests unreliable on travis')
