import unittest

from mock import patch

from pyuploadcare import UploadCare, UploadCareException
from pyuploadcare.file import File


class MockResponse():
    def __init__(self, status, data):
        self.status = status
        self.data = data

    def read(self):
        return self.data


class UploadCareTest(unittest.TestCase):
    @patch('httplib.HTTPConnection', autospec=True)
    def test_request_headers(self, con):
        def request_v01(verb, uri, content, headers):
            self.assertIn('Accept', headers)
            self.assertIn('User-Agent', headers)
            self.assertEqual(headers['Accept'],
                             'application/json')
            self.assertEqual(headers['User-Agent'],
                             'pyuploadcare/0.1')

        def request_v02(verb, uri, content, headers):
            self.assertIn('Accept', headers)
            self.assertIn('User-Agent', headers)
            self.assertEqual(headers['Accept'],
                             'application/vnd.uploadcare-v0.2+json')
            self.assertEqual(headers['User-Agent'],
                             'pyuploadcare/0.2')

        con.return_value.getresponse.return_value = MockResponse(200, '[]')
        con.return_value.request = request_v02

        ucare = UploadCare('pub', 'secret')
        ucare.make_request('GET', '/files/')

        con.return_value.request = request_v01
        ucare = UploadCare('pub', 'secret', api_version='0.1')
        ucare.make_request('GET', '/files/')
