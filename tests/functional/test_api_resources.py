# coding: utf-8
from __future__ import unicode_literals
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import datetime
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from mock import patch
from dateutil.tz import tzutc

from pyuploadcare.api_resources import File, FileGroup
from pyuploadcare.exceptions import InvalidRequestError
from .utils import MockResponse, api_response_from_file


class FileRegexTest(unittest.TestCase):

    def test_value_error_when_uuid_is_bad(self):
        file_serialized = 'blah'
        self.assertRaises(InvalidRequestError, File, file_serialized)

    def test_only_uuid(self):
        file_serialized = '3addab78-6368-4c55-ac08-22412b6a2a4c'
        expected_cdn_url = 'http://www.ucarecdn.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_arbitrary_domain(self):
        file_serialized = 'http://example.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'
        expected_cdn_url = 'http://www.ucarecdn.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_crop_effect(self):
        file_serialized = 'cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'
        expected_cdn_url = 'http://www.ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_crop_effect_and_arbitrary_domain(self):
        file_serialized = 'http://www.ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'
        expected_cdn_url = file_serialized

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)


class FileDateMethodsTest(unittest.TestCase):

    def setUp(self):
        self.file = File('a771f854-c2cb-408a-8c36-71af77811f3b')

    def test_datetime_stored_is_none(self):
        self.file._info_cache = {'datetime_stored': ''}
        self.assertIsNone(self.file.datetime_stored())

    def test_datetime_stored_is_utc(self):
        self.file._info_cache = {'datetime_stored': '2013-02-05T12:56:12.006Z'}
        expected_datetime = datetime.datetime(
            year=2013, month=2, day=5, hour=12, minute=56, second=12,
            microsecond=6000, tzinfo=tzutc())
        self.assertEqual(self.file.datetime_stored(), expected_datetime)

    def test_datetime_removed_is_none(self):
        self.file._info_cache = {}
        self.assertIsNone(self.file.datetime_removed())

    def test_datetime_removed_is_utc(self):
        self.file._info_cache = {'datetime_removed': '2013-02-05T12:56:12.006Z'}
        expected_datetime = datetime.datetime(
            year=2013, month=2, day=5, hour=12, minute=56, second=12,
            microsecond=6000, tzinfo=tzutc())
        self.assertEqual(self.file.datetime_removed(), expected_datetime)

    def test_datetime_uploaded_is_none(self):
        self.file._info_cache = {'datetime_uploaded': None}
        self.assertIsNone(self.file.datetime_uploaded())

    def test_datetime_uploaded_is_utc(self):
        self.file._info_cache = {'datetime_uploaded': '2013-02-05T12:56:12.006Z'}
        expected_datetime = datetime.datetime(
            year=2013, month=2, day=5, hour=12, minute=56, second=12,
            microsecond=6000, tzinfo=tzutc())
        self.assertEqual(self.file.datetime_uploaded(), expected_datetime)


class FileGroupRegexTest(unittest.TestCase):

    def test_value_error_when_uuid_is_bad(self):
        group_id = 'blah'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_value_error_when_group_id_has_not_files_qty(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_value_error_when_group_id_has_chars_instead_of_files_qty(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~blah'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_value_error_when_group_id_has_zero_files(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~0'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_valid_group_id(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~12'
        expected_cdn_url = 'http://www.ucarecdn.com/d5f45851-3a58-41a4-b76c-356e22837a2f~12/'

        group = FileGroup(group_id)
        self.assertEqual(group.cdn_url, expected_cdn_url)
        self.assertEqual(len(group), 12)

    def test_extracting_group_id_from_url(self):
        cdn_url = 'http://www.ucarecdn.com/d5f45851-3a58-41a4-b76c-356e22837a2f~12/'
        expected_group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~12'

        group = FileGroup(cdn_url)
        self.assertEqual(group.id, expected_group_id)
        self.assertEqual(len(group), 12)


class FileGroupDateMethodsTest(unittest.TestCase):

    def setUp(self):
        self.group = FileGroup('0513dda0-582f-447d-846f-096e5df9e2bb~2')

    def test_datetime_stored_is_none(self):
        self.group._info_cache = {'datetime_stored': ''}
        self.assertIsNone(self.group.datetime_stored())

    def test_datetime_stored_is_utc(self):
        self.group._info_cache = {'datetime_stored': '2013-04-03T12:01:28.714Z'}
        expected_datetime = datetime.datetime(
            year=2013, month=4, day=3, hour=12, minute=1, second=28,
            microsecond=714000, tzinfo=tzutc())
        self.assertEqual(self.group.datetime_stored(), expected_datetime)

    def test_datetime_created_is_none(self):
        self.group._info_cache = {'datetime_created': ''}
        self.assertIsNone(self.group.datetime_created())

    def test_datetime_created_is_utc(self):
        self.group._info_cache = {'datetime_created': '2013-04-03T12:01:28.714Z'}
        expected_datetime = datetime.datetime(
            year=2013, month=4, day=3, hour=12, minute=1, second=28,
            microsecond=714000, tzinfo=tzutc())
        self.assertEqual(self.group.datetime_created(), expected_datetime)


class FileGroupAsContainerTypeTest(unittest.TestCase):

    @patch('requests.sessions.Session.request', autospec=True)
    def setUp(self, request):
        request.return_value = MockResponse(
            status=200,
            data=api_response_from_file('group_files.json')
        )

        self.group = FileGroup(
            cdn_url_or_group_id='0513dda0-582f-447d-846f-096e5df9e2bb~2'
        )
        # It is necessary to avoid api call in tests below.
        self.group.update_info()

    def test_positive_index(self):
        self.assertIsInstance(self.group[0], File)

    def test_negative_index(self):
        self.assertIsNone(self.group[-1])

    def test_index_is_out_of_range(self):
        with self.assertRaises(IndexError):
            self.group[2]

    def test_non_int_index(self):
        with self.assertRaises(TypeError):
            self.group['a']

    def test_iteration(self):
        [file_ for file_ in self.group]

    def test_slice_is_not_supported(self):
        with self.assertRaises(TypeError):
            self.group[0:99]

    def test_len(self):
        self.assertEqual(len(self.group), 2)

    def test_immutability(self):
        with self.assertRaises(TypeError):
            self.group[0] = 123


class StoreFileGroupTest(unittest.TestCase):

    @patch('requests.sessions.Session.request', autospec=True)
    def test_successful_store(self, request):
        group = FileGroup(
            cdn_url_or_group_id='0513dda0-582f-447d-846f-096e5df9e2bb~2'
        )
        group._info_cache = {"datetime_stored": None}
        # PUT /api/groups/{group_id}/storage/
        request.return_value = MockResponse(
            status=200,
            data='{"datetime_stored": "2013-04-03T12:01:28.714Z"}')
        group.store()

        self.assertEqual(request.call_count, 1)

    @patch('requests.sessions.Session.request', autospec=True)
    def test_do_not_store_twice(self, request):
        group = FileGroup(
            cdn_url_or_group_id='0513dda0-582f-447d-846f-096e5df9e2bb~2'
        )
        # GET /api/groups/{group_id}/
        request.return_value = MockResponse(
            status=200,
            data='{"datetime_stored": "2013-04-03T12:01:28.714Z"}')
        group.store()
        group.store()

        self.assertEqual(request.call_count, 1)


class FileCDNUrlsTest(unittest.TestCase):

    def setUp(self):
        self.group = FileGroup(
            cdn_url_or_group_id='0513dda0-582f-447d-846f-096e5df9e2bb~2'
        )

    @patch('requests.sessions.Session.request', autospec=True)
    def test_no_api_requests(self, request):
        request.return_value = MockResponse(status=200, data='{}')
        self.group.file_cdn_urls

        self.assertFalse(request.called)

    def test_two_files_are_in_group(self):
        expected_file_cdn_urls = [
            'http://www.ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/nth/0/',
            'http://www.ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/nth/1/',
        ]
        self.assertEqual(self.group.file_cdn_urls, expected_file_cdn_urls)


class FileGroupCreateTest(unittest.TestCase):

    def test_invalid_request_error_if_iterable_is_empty(self):
        self.assertRaises(InvalidRequestError, FileGroup.create, [])

    def test_type_error_if_non_iterable(self):
        self.assertRaises(TypeError, FileGroup.create, None)

    def test_invalid_request_error_if_non_file_instance(self):
        files = (
            File('6c5e9526-b0fe-4739-8975-72e8d5ee6342'),
            None,
        )
        self.assertRaises(InvalidRequestError, FileGroup.create, files)

    def test_invalid_request_error_if_iterable_is_dict(self):
        files = {
            'file_1': File('6c5e9526-b0fe-4739-8975-72e8d5ee6342'),
            'file_2': File('a771f854-c2cb-408a-8c36-71af77811f3b'),
        }
        self.assertRaises(InvalidRequestError, FileGroup.create, files)

    @patch('requests.sessions.Session.request', autospec=True)
    def test_group_successfully_created(self, request):
        json_response = """{
            "id": "0513dda0-582f-447d-846f-096e5df9e2bb~1",
            "files_count": 1,
            "files": [
                {"uuid": "0cea5a61-f976-47d9-815a-e787f52aeba1"}
            ]
        }
        """
        request.return_value = MockResponse(status=200, data=json_response)

        files = (
            File('0cea5a61-f976-47d9-815a-e787f52aeba1'),
        )
        group = FileGroup.create(files)

        self.assertIsInstance(group, FileGroup)
        self.assertEqual(len(group), 1)
        self.assertEqual(group[0].uuid, '0cea5a61-f976-47d9-815a-e787f52aeba1')
