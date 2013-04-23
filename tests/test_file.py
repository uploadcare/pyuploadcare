# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from mock import patch

from pyuploadcare.api_resources import File, FileGroup
from tests.utils import MockResponse, api_response_from_file


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
