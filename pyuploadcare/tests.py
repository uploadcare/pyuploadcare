import unittest
import os
import json
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project'

from mock import patch
from django.test.utils import override_settings
from django import forms

from pyuploadcare import UploadCare, UploadCareException
from pyuploadcare.file import File
from pyuploadcare.dj import forms as uc_forms


class MockResponse():
    def __init__(self, status, data):
        self.status_code = status
        self.content = data

    @property
    def json(self):
        """Returns the json-encoded content of a response, if any."""
        try:
            return json.loads(self.content)
        except ValueError:
            return None


class UploadCareTest(unittest.TestCase):

    @patch('requests.request', autospec=True)
    def test_raises(self, request):
        request.return_value = MockResponse(404, '{}')
        ucare = UploadCare('pub', 'secret')

        with self.assertRaises(UploadCareException):
            ucare.make_request('GET', '/files/')

        request.return_value = MockResponse(200, 'meh')
        with self.assertRaises(ValueError) as cm:
            ucare.make_request('GET', '/files/')
        self.assertEqual('no json in response', cm.exception.message)

    @patch('requests.request', autospec=True)
    def test_request_headers(self, request):

        request.return_value = MockResponse(200, '[]')

        ucare = UploadCare('pub', 'secret')
        ucare.make_request('GET', '/files/')
        headers = request.call_args[1]['headers']
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'],
                         'application/vnd.uploadcare-v0.2+json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.7')

        ucare = UploadCare('pub', 'secret', api_version='0.1')
        ucare.make_request('GET', '/files/')
        headers = request.call_args[1]['headers']
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'], 'application/json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.7')

    def test_uri_builders(self):
        ucare = UploadCare('pub', 'secret')
        path = ucare._build_api_path('/files/?asd=1')
        uri = ucare._build_api_uri(path)
        self.assertEqual(path, '/files/?asd=1')
        self.assertEqual(uri, 'http://api.uploadcare.com/files/?asd=1')

        ucare = UploadCare('pub', 'secret', api_base='http://example.com/api')
        path = ucare._build_api_path('/files/?asd=1')
        uri = ucare._build_api_uri(path)
        self.assertEqual(path, '/api/files/?asd=1')
        self.assertEqual(uri, 'http://example.com/api/files/?asd=1')


class FileTest(unittest.TestCase):
    @patch('requests.request', autospec=True)
    def test_store_timeout(self, request):
        ucare = UploadCare('pub', 'secret')
        response = MockResponse(200, '{"on_s3": false}')
        request.return_value = response

        f = File('uuid', ucare)
        with self.assertRaises(Exception) as cm:
            f.store(wait=True, timeout=1)
        self.assertEqual('timed out trying to store',
                         cm.exception.message)

        response = MockResponse(200, '{"on_s3": true}')
        request.return_value = response
        f.store(wait=True, timeout=1)

    @patch('requests.request', autospec=True)
    def test_url_caching(self, request):
        """Test that known url is cached and no requests are made"""

        ucare = UploadCare('pub', 'secret')
        uuid = '6c5e9526-b0fe-4739-8975-72e8d5ee6342'
        request.return_value = MockResponse(200,
            '{"original_file_url": "meh"}')

        self.assertEqual(0, len(request.mock_calls))

        f = ucare.file(uuid)
        self.assertEqual('meh', f.url)
        self.assertEqual(1, len(request.mock_calls))

        fake_url = 'http://i-am-the-file/{}/'.format(uuid)
        f = ucare.file(fake_url)
        self.assertEqual(fake_url, f.url)
        # no additional calls are made
        self.assertEqual(1, len(request.mock_calls))


class TestFormFields(unittest.TestCase):

    @override_settings(UPLOADCARE={'pub_key': 'asdf', 'secret': 'qwer'})
    def test_default_form_field(self):

        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField()

        f = SomeForm()
        self.assertRegexpMatches(str(f.media),
            'http://fastatic\.uploadcare\.com/widget/[\d\.]+/uploadcare-[\d\.]+line\.en\.js')
        self.assertIn('role="uploadcare-line-uploader"', str(f['ff']))
        self.assertIn('data-public-key="asdf"', str(f['ff']))
        self.assertIn('type="hidden"', str(f['ff']))

    @override_settings(UPLOADCARE={'pub_key': 'asdf', 'secret': 'qwer'})
    def test_form_field_custom_attrs(self):

        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField(
                widget=uc_forms.FileWidget(attrs={'role': 'role'}))

        f = SomeForm()
        self.assertRegexpMatches(str(f.media),
            'http://fastatic\.uploadcare\.com/widget/[\d\.]+/uploadcare-[\d\.]+line\.en\.js')
        self.assertIn('role="role"', str(f['ff']))
        self.assertIn('data-public-key="asdf"', str(f['ff']))
        self.assertIn('type="hidden"', str(f['ff']))
