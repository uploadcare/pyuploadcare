# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from mock import patch

from pyuploadcare.api_resources import File, FileGroup
from pyuploadcare.exceptions import InvalidRequestError
from tests.utils import MockResponse, api_response_from_file


class FileRegexTest(unittest.TestCase):

    def test_value_error_when_uuid_is_bad(self):
        file_serialized = 'blah'
        self.assertRaises(InvalidRequestError, File, file_serialized)

    def test_only_uuid(self):
        file_serialized = '3addab78-6368-4c55-ac08-22412b6a2a4c'
        expected_cdn_url = 'https://ucarecdn.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_arbitrary_domain(self):
        file_serialized = 'http://example.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'
        expected_cdn_url = 'https://ucarecdn.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_crop_effect(self):
        file_serialized = 'cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'
        expected_cdn_url = 'https://ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_crop_effect_and_arbitrary_domain(self):
        file_serialized = 'https://ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'
        expected_cdn_url = file_serialized

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)


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
        expected_cdn_url = 'https://ucarecdn.com/d5f45851-3a58-41a4-b76c-356e22837a2f~12/'

        group = FileGroup(group_id)
        self.assertEqual(group.cdn_url, expected_cdn_url)
        self.assertEqual(len(group), 12)

    def test_extracting_group_id_from_url(self):
        cdn_url = 'https://ucarecdn.com/d5f45851-3a58-41a4-b76c-356e22837a2f~12/'
        expected_group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~12'

        group = FileGroup(cdn_url)
        self.assertEqual(group.id, expected_group_id)
        self.assertEqual(len(group), 12)


class FileGroupAsContainerTypeTest(unittest.TestCase):

    @patch('requests.request', autospec=True)
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

    @patch('requests.request', autospec=True)
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

    @patch('requests.request', autospec=True)
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

    @patch('requests.request', autospec=True)
    def test_no_api_requests(self, request):
        request.return_value = MockResponse(status=200, data='{}')
        self.group.file_cdn_urls

        self.assertFalse(request.called)

    def test_two_files_are_in_group(self):
        expected_file_cdn_urls = [
            'https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/nth/0/',
            'https://ucarecdn.com/0513dda0-582f-447d-846f-096e5df9e2bb~2/nth/1/',
        ]
        self.assertEqual(self.group.file_cdn_urls, expected_file_cdn_urls)
