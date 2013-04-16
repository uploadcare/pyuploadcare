# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch

from pyuploadcare.ucare_cli import ucare_argparser, ucare_list
from .tests import MockResponse


def arg_namespace(arguments_str):
    return ucare_argparser().parse_args(arguments_str.split())


class UcareListTest(unittest.TestCase):

    @patch('requests.request', autospec=True)
    def test_no_args(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/')
        )

    @patch('requests.request', autospec=True)
    def test_page_2(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --page 2'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?page=2')
        )

    @patch('requests.request', autospec=True)
    def test_limit_10(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --limit 10'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?limit=10')
        )

    @patch('requests.request', autospec=True)
    def test_kept_all(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --kept all'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?kept=all')
        )

    @patch('requests.request', autospec=True)
    def test_kept_true(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --kept true'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?kept=true')
        )

    @patch('requests.request', autospec=True)
    def test_kept_false(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --kept false'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?kept=false')
        )

    @patch('requests.request', autospec=True)
    def test_removed_all(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --removed all'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?removed=all')
        )

    @patch('requests.request', autospec=True)
    def test_removed_true(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --removed true'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?removed=true')
        )

    @patch('requests.request', autospec=True)
    def test_removed_false(self, request):
        request.return_value = MockResponse(status=200)

        ucare_list(arg_namespace('list --removed false'))

        self.assertEqual(
            request.mock_calls[0][1],
            ('GET', 'https://api.uploadcare.com/files/?removed=false')
        )
