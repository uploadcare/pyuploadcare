# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from mock import patch

from pyuploadcare import conf
from pyuploadcare.api import rest_request
from pyuploadcare.exceptions import APIError, InvalidRequestError
from tests.utils import MockResponse


class RESTClientTest(unittest.TestCase):

    def tearDown(self):
        conf.api_version = '0.2'
        conf.api_base = 'https://api.uploadcare.com/'

    @patch('requests.request', autospec=True)
    def test_raises(self, request):
        request.return_value = MockResponse(404, '{}')
        with self.assertRaises(InvalidRequestError):
            rest_request('GET', '/files/')

        request.return_value = MockResponse(200, 'meh')
        with self.assertRaises(APIError) as cm:
            rest_request('GET', '/files/')

        self.assertEqual('API error: No JSON object could be decoded',
                         cm.exception.message)

    @patch('requests.request', autospec=True)
    def test_request_headers(self, request):
        request.return_value = MockResponse(200, '[]')

        rest_request('GET', '/files/')
        headers = request.call_args[1]['headers']
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'],
                         'application/vnd.uploadcare-v0.2+json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.19')

        conf.api_version = '0.1'
        rest_request('GET', '/files/')
        headers = request.call_args[1]['headers']
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'], 'application/vnd.uploadcare-v0.1+json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.19')
