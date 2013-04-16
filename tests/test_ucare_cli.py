# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from pyuploadcare.ucare_cli import (
    ucare_argparser, list_files, get_file, store_file, delete_file,
)
from .tests import MockResponse


def arg_namespace(arguments_str):
    return ucare_argparser().parse_args(arguments_str.split())


class UcareListTest(unittest.TestCase):

    @patch('requests.request', autospec=True)
    def test_no_args(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/')
        )

    @patch('requests.request', autospec=True)
    def test_page_2(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --page 2'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?page=2')
        )

    @patch('requests.request', autospec=True)
    def test_limit_10(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --limit 10'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?limit=10')
        )

    @patch('requests.request', autospec=True)
    def test_kept_all(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --kept all'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?kept=all')
        )

    @patch('requests.request', autospec=True)
    def test_kept_true(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --kept true'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?kept=true')
        )

    @patch('requests.request', autospec=True)
    def test_kept_false(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --kept false'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?kept=false')
        )

    @patch('requests.request', autospec=True)
    def test_removed_all(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --removed all'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?removed=all')
        )

    @patch('requests.request', autospec=True)
    def test_removed_true(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --removed true'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?removed=true')
        )

    @patch('requests.request', autospec=True)
    def test_removed_false(self, request):
        request.return_value = MockResponse(status=200)

        list_files(arg_namespace('list --removed false'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?removed=false')
        )


class UcareGetTest(unittest.TestCase):

    @patch('requests.request', autospec=True)
    def test_get_by_uuid(self, request):
        request.return_value = MockResponse(status=200)

        get_file(arg_namespace('get 6c5e9526-b0fe-4739-8975-72e8d5ee6342'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/6c5e9526-b0fe-4739-8975-72e8d5ee6342/')
        )

    @patch('requests.request', autospec=True)
    def test_get_by_cdn_url(self, request):
        request.return_value = MockResponse(status=200)

        get_file(arg_namespace('get https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/6c5e9526-b0fe-4739-8975-72e8d5ee6342/')
        )


class UcareStoreTest(unittest.TestCase):

    def test_parse_wait_arg(self):
        args = arg_namespace('store --wait 6c5e9526-b0fe-4739-8975-72e8d5ee6342')
        self.assertTrue(args.wait)

    def test_wait_is_true_by_default(self):
        args = arg_namespace('store 6c5e9526-b0fe-4739-8975-72e8d5ee6342')
        self.assertTrue(args.wait)

    def test_parse_no_wait_arg(self):
        args = arg_namespace('store --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342')
        self.assertFalse(args.wait)

    @patch('requests.request', autospec=True)
    def test_no_wait(self, request):
        request.return_value = MockResponse(
            status=200,
            data='{"on_s3": true, "last_keep_claim": "now"}'
        )

        store_file(arg_namespace('store --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('PUT', 'https://api.uploadcare.com/files/6c5e9526-b0fe-4739-8975-72e8d5ee6342/storage/')
        )


class UcareDeleteTest(unittest.TestCase):

    def test_parse_wait_arg(self):
        args = arg_namespace('delete --wait 6c5e9526-b0fe-4739-8975-72e8d5ee6342')
        self.assertTrue(args.wait)

    def test_wait_is_true_by_default(self):
        args = arg_namespace('delete 6c5e9526-b0fe-4739-8975-72e8d5ee6342')
        self.assertTrue(args.wait)

    def test_parse_no_wait_arg(self):
        args = arg_namespace('delete --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342')
        self.assertFalse(args.wait)

    @patch('requests.request', autospec=True)
    def test_no_wait(self, request):
        request.return_value = MockResponse(
            status=200,
            data='{"on_s3": true, "last_keep_claim": "now"}'
        )

        delete_file(arg_namespace('delete --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('DELETE', 'https://api.uploadcare.com/files/6c5e9526-b0fe-4739-8975-72e8d5ee6342/')
        )
