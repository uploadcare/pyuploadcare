# coding: utf-8
from __future__ import unicode_literals
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from tempfile import NamedTemporaryFile
from datetime import datetime
import time

from pyuploadcare import conf
from pyuploadcare.api_resources import File, FileGroup, FileList

from .utils import upload_tmp_txt_file, create_file_group, skip_on_travis


class FileUploadTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'

        self.tmp_config_file = NamedTemporaryFile(mode='w+t')

    def tearDown(self):
        conf.pub_key = None

        self.tmp_config_file.close()

    def test_successful_upload(self):
        file_ = File.upload(self.tmp_config_file)
        self.assertIsInstance(file_, File)


class FileUploadFromUrlTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'

    def tearDown(self):
        conf.pub_key = None

    def test_get_some_token(self):
        file_from_url = File.upload_from_url(
            'https://github.com/images/error/angry_unicorn.png'
        )
        self.assertTrue(file_from_url.token)

    @skip_on_travis
    def test_successful_upload_from_url(self):
        file_from_url = File.upload_from_url(
            'https://github.com/images/error/angry_unicorn.png'
        )

        timeout = 30
        time_started = time.time()

        while time.time() - time_started < timeout:
            status = file_from_url.update_info()['status']
            if status in ('success', 'failed', 'error'):
                break
            time.sleep(1)

        self.assertIsInstance(file_from_url.get_file(), File)


class FileInfoTest(unittest.TestCase):

    file_ = upload_tmp_txt_file(content='hello')

    def setUp(self):
        conf.pub_key = 'demopublickey'
        conf.secret = 'demoprivatekey'

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_info_is_non_empty_dict(self):
        self.assertIsInstance(self.file_.info(), dict)
        self.assertTrue(self.file_.info())

    def test_original_filename_starts_with_tmp(self):
        self.assertTrue(self.file_.filename().startswith('tmp'))

    def test_datetime_stored_is_none(self):
        self.assertIsNone(self.file_.datetime_stored())

    def test_datetime_removed_is_none(self):
        self.assertIsNone(self.file_.datetime_removed())

    def test_datetime_uploaded_is_datetime_instance(self):
        self.assertIsInstance(self.file_.datetime_uploaded(), datetime)

    def test_file_is_not_stored(self):
        self.assertFalse(self.file_.is_stored())

    def test_file_is_not_removed(self):
        self.assertFalse(self.file_.is_removed())

    def test_file_is_not_image(self):
        self.assertFalse(self.file_.is_image())

    @skip_on_travis
    def test_file_should_be_ready_in_5_seconds_after_upload(self):
        timeout = 5
        time_started = time.time()

        while time.time() - time_started < timeout:
            if self.file_.is_ready():
                break
            time.sleep(1)
            self.file_.update_info()

        self.assertTrue(self.file_.is_ready())

    def test_file_size_is_5_bytes(self):
        # "hello" + new line
        self.assertEqual(self.file_.size(), 5)

    def test_mime_type_is_application_octet_stream(self):
        self.assertEqual(self.file_.mime_type(), 'application/octet-stream')


class FileStoreTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'
        conf.secret = 'demoprivatekey'

        self.file_ = upload_tmp_txt_file(content='hello')

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_successful_store(self):
        self.assertFalse(self.file_.is_stored())

        self.file_.store()

        self.assertTrue(self.file_.is_stored())


class FileDeleteTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'
        conf.secret = 'demoprivatekey'

        self.file_ = upload_tmp_txt_file(content='hello')

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_successful_delete(self):
        self.assertFalse(self.file_.is_removed())

        self.file_.delete()

        self.assertTrue(self.file_.is_removed())


class FileGroupCreateTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_successful_create(self):
        files = [
            upload_tmp_txt_file(content='hello'),
        ]
        group = FileGroup.create(files)
        self.assertIsInstance(group, FileGroup)


class FileGroupInfoTest(unittest.TestCase):

    group = create_file_group(files_qty=1)

    def setUp(self):
        conf.pub_key = 'demopublickey'
        conf.secret = 'demoprivatekey'

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_info_is_non_empty_dict(self):
        self.assertIsInstance(self.group.info(), dict)
        self.assertTrue(self.group.info())

    def test_datetime_stored_is_none(self):
        self.assertIsNone(self.group.datetime_stored())

    def test_datetime_created_is_datetime_instance(self):
        self.assertIsInstance(self.group.datetime_created(), datetime)

    def test_group_is_not_stored(self):
        self.assertFalse(self.group.is_stored())


class FileGroupStoreTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'
        conf.secret = 'demoprivatekey'

        self.group = create_file_group(files_qty=1)

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_successful_store(self):
        self.assertFalse(self.group.is_stored())

        self.group.store()

        self.assertTrue(self.group.is_stored())


class FileListRetrieveTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'
        conf.secret = 'demoprivatekey'

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_get_only_one_file(self):
        result = FileList.retrieve(page=1, limit=1)
        if result['results']:
            self.assertEqual(len(result['results']), 1)

    def test_get_only_stored_file(self):
        result = FileList.retrieve(page=1, limit=1, stored=True)
        if result['results']:
            file_info = result['results'][0]
            self.assertIsNotNone(file_info['datetime_stored'])

    def test_get_only_non_stored_file(self):
        result = FileList.retrieve(page=1, limit=1, stored=False)
        if result['results']:
            file_info = result['results'][0]
            self.assertIsNone(file_info['datetime_stored'])

    def test_get_only_removed_file(self):
        result = FileList.retrieve(page=1, limit=1, removed=True)
        if result['results']:
            file_info = result['results'][0]
            self.assertIsNotNone(file_info['datetime_removed'])

    def test_get_only_non_removed_file(self):
        result = FileList.retrieve(page=1, limit=1, removed=False)
        if result['results']:
            file_info = result['results'][0]
            self.assertIsNone(file_info['datetime_removed'])

    def test_get_only_stored_removed_file(self):
        result = FileList.retrieve(page=1, limit=1, stored=True, removed=True)
        if result['results']:
            file_info = result['results'][0]
            self.assertIsNotNone(file_info['datetime_stored'])
            self.assertIsNotNone(file_info['datetime_removed'])


class FileListIterationTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = 'demopublickey'
        conf.secret = 'demoprivatekey'

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

    def test_iteration_over_all_files(self):
        files = list(file_ for file_ in FileList())
        self.assertTrue(len(files) >= 0)

    def test_iteration_over_limited_count_of_files(self):
        create_file_group(files_qty=3)

        files = list(file_ for file_ in FileList(count=2))
        self.assertEqual(len(files), 2)

    def test_iteration_over_stored_files(self):
        for file_ in FileList(stored=True):
            self.assertTrue(file_.is_stored())

    def test_iteration_over_removed_files(self):
        for file_ in FileList(removed=True):
            self.assertTrue(file_.is_removed())

    def test_iteration_over_stored_removed_files(self):
        for file_ in FileList(stored=True, removed=True):
            self.assertTrue(file_.is_stored())
            self.assertTrue(file_.is_removed())
