# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from mock import patch

from pyuploadcare import UploadCare
from pyuploadcare.exceptions import (
    InvalidRequestError, TimeoutError,
)
from pyuploadcare.file import File, FileGroup
from tests.utils import MockResponse, api_response_from_file


class FileTest(unittest.TestCase):

    @patch('requests.head', autospec=True)
    @patch('requests.request', autospec=True)
    def test_store_timeout(self, request, head):
        ucare = UploadCare('pub', 'secret')
        api_response = MockResponse(200, '{"on_s3": false, "last_keep_claim": null}')
        request.return_value = api_response
        cdn_response = MockResponse(200)
        head.return_value = cdn_response

        f = File('6c5e9526-b0fe-4739-8975-72e8d5ee6342', ucare)
        with self.assertRaises(TimeoutError) as cm:
            f.store(wait=True, timeout=0.2)
        self.assertEqual('timed out trying to store',
                         cm.exception.message)

        response = MockResponse(200, '{"on_s3": true, "last_keep_claim": "now"}')
        request.return_value = response
        f.store(wait=True, timeout=1)

    @patch('requests.request', autospec=True)
    def test_delete_timeout(self, request):
        ucare = UploadCare('pub', 'secret')
        response = MockResponse(200, '{"removed": null}')
        request.return_value = response

        f = File('6c5e9526-b0fe-4739-8975-72e8d5ee6342', ucare)
        with self.assertRaises(TimeoutError) as cm:
            f.delete(wait=True, timeout=0.2)
        self.assertEqual('timed out trying to delete',
                         cm.exception.message)

        response = MockResponse(200, '{"removed": "now"}')
        request.return_value = response
        f.delete(wait=True, timeout=1)

    @patch('requests.request', autospec=True)
    def test_url_caching(self, request):
        """Test that known url is cached and no requests are made"""

        ucare = UploadCare('pub', 'secret')
        uuid = '6c5e9526-b0fe-4739-8975-72e8d5ee6342'
        request.return_value = MockResponse(
            status=200,
            data='{"original_file_url": "meh"}'
        )

        self.assertEqual(0, len(request.mock_calls))

        f = ucare.file(uuid)
        self.assertEqual('meh', f.url)
        self.assertEqual(1, len(request.mock_calls))

        fake_url = 'http://i-am-the-file/{0}/'.format(uuid)
        f = ucare.file(fake_url)
        self.assertEqual(fake_url, f.url)
        # no additional calls are made
        self.assertEqual(1, len(request.mock_calls))

    @patch('requests.head', autospec=True)
    @patch('requests.request', autospec=True)
    def test_cdn_urls(self, request, head):
        ucare = UploadCare('pub', 'secret')
        uuid = '6c5e9526-b0fe-4739-8975-72e8d5ee6342'
        f = ucare.file(uuid)
        api_response = MockResponse(200, '{"on_s3": true, "last_keep_claim": true}')
        request.return_value = api_response
        cdn_response = MockResponse(200)
        head.return_value = cdn_response
        f.store(wait=True, timeout=1)

        self.assertEqual(f.cdn_url, 'https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/')
        self.assertEqual(f.resized_40x40, 'https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/-/resize/40x40/')
        self.assertEqual(f.resized_x40, 'https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/-/resize/x40/')
        self.assertEqual(f.resized_40x, 'https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/-/resize/40/')
        self.assertEqual(f.cropped_40x40, 'https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/-/crop/40x40/')
        with self.assertRaises(InvalidRequestError):
            f.cropped_40
        with self.assertRaises(InvalidRequestError):
            f.resized_
        with self.assertRaises(InvalidRequestError):
            f.resized_1x1x1

    @patch('requests.head', autospec=True)
    @patch('requests.request', autospec=True)
    def test_ensure_on_cdn_raises(self, request, head):
        ucare = UploadCare('pub', 'secret')
        uuid = '6c5e9526-b0fe-4739-8975-72e8d5ee6342'
        f = ucare.file(uuid)
        api_response = MockResponse(
            status=200, data='{"on_s3": true, "last_keep_claim": true}'
        )
        request.return_value = api_response
        cdn_response = MockResponse(404)
        head.return_value = cdn_response
        with self.assertRaises(TimeoutError) as cm:
            f.store(wait=True, timeout=0.1)
        self.assertEqual('timed out waiting for file appear on cdn', cm.exception.message)


class FileGroupAsContainerTypeTest(unittest.TestCase):

    @patch('requests.request', autospec=True)
    def setUp(self, request):
        request.return_value = MockResponse(
            status=200,
            data=api_response_from_file('group_files.json')
        )

        self.group = FileGroup(
            cdn_url_or_group_id='0513dda0-582f-447d-846f-096e5df9e2bb~2',
            ucare=UploadCare('pub', 'secret')
        )
        # It is necessary to avoid api call in tests below.
        self.group.update_info()

    def test_positive_index(self):
        self.assertIsInstance(self.group[0], File)

    def test_negative_index(self):
        self.assertIsInstance(self.group[-1], File)

    def test_index_is_out_of_range(self):
        with self.assertRaises(IndexError):
            self.group[2]

    def test_non_int_index(self):
        with self.assertRaises(TypeError):
            self.group['a']

    def test_slice(self):
        for file_ in self.group[0:99]:
            self.assertIsInstance(file_, File)

    def test_len(self):
        self.assertEqual(len(self.group), 2)

    def test_immutability(self):
        with self.assertRaises(TypeError):
            self.group[0] = 123


class StoreFileGroupTest(unittest.TestCase):

    @patch('requests.request', autospec=True)
    def test_successful_store(self, request):
        group = FileGroup(
            cdn_url_or_group_id='0513dda0-582f-447d-846f-096e5df9e2bb~2',
            ucare=UploadCare('pub', 'secret')
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
            cdn_url_or_group_id='0513dda0-582f-447d-846f-096e5df9e2bb~2',
            ucare=UploadCare('pub', 'secret')
        )
        # GET /api/groups/{group_id}/
        request.return_value = MockResponse(
            status=200,
            data='{"datetime_stored": "2013-04-03T12:01:28.714Z"}')
        group.store()
        group.store()

        self.assertEqual(request.call_count, 1)
