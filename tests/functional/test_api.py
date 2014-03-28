# coding: utf-8
from __future__ import unicode_literals
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
from .utils import MockResponse


class RESTClientTest(unittest.TestCase):

    def tearDown(self):
        conf.api_version = '0.3'

    @patch('requests.sessions.Session.request', autospec=True)
    def test_raises(self, request):
        request.return_value = MockResponse(404, b'{}')
        with self.assertRaises(InvalidRequestError):
            rest_request('GET', 'files/')

        request.return_value = MockResponse(200, b'meh')
        with self.assertRaises(APIError) as cm:
            rest_request('GET', 'files/')

        self.assertEqual('No JSON object could be decoded',
                         cm.exception.data)

    @patch('requests.sessions.Session.request', autospec=True)
    def test_request_headers(self, request):
        request.return_value = MockResponse(200, b'[]')

        rest_request('GET', 'files/')
        headers = request.call_args[1]['headers']
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'],
                         'application/vnd.uploadcare-v0.3+json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/1.2.2')

        conf.api_version = '0.1'
        rest_request('GET', 'files/')
        headers = request.call_args[1]['headers']
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'], 'application/vnd.uploadcare-v0.1+json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/1.2.2')
