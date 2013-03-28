import unittest
import os
import json
import re
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from mock import patch
from django.test.utils import override_settings
from django import forms

from pyuploadcare import UploadCare, UploadCareException, APIError
from pyuploadcare.file import File
from pyuploadcare.dj import forms as uc_forms

class _AssertRaisesContext(object):
    """A context manager used to implement TestCase.assertRaises* methods."""

    def __init__(self, expected, test_case, expected_regexp=None):
        self.expected = expected
        self.failureException = test_case.failureException
        self.expected_regexp = expected_regexp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            try:
                exc_name = self.expected.__name__
            except AttributeError:
                exc_name = str(self.expected)
            raise self.failureException(
                "{0} not raised".format(exc_name))
        if not issubclass(exc_type, self.expected):
            # let unexpected exceptions pass through
            return False
        self.exception = exc_value # store for later retrieval
        if self.expected_regexp is None:
            return True

        expected_regexp = self.expected_regexp
        if isinstance(expected_regexp, basestring):
            expected_regexp = re.compile(expected_regexp)
        if not expected_regexp.search(str(exc_value)):
            raise self.failureException('"%s" does not match "%s"' %
                     (expected_regexp.pattern, str(exc_value)))
        return True


class ModernTestCase(unittest.TestCase):
    def _assertRaises(self, excClass, callableObj=None, *args, **kwargs):
        context = _AssertRaisesContext(excClass, self)
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)

    def _assertRegexpMatches(self, text, expected_regexp, msg=None):
        """Fail the test unless the text matches the regular expression."""
        if isinstance(expected_regexp, basestring):
            expected_regexp = re.compile(expected_regexp)
        if not expected_regexp.search(text):
            msg = msg or "Regexp didn't match"
            msg = '%s: %r not found in %r' % (msg, expected_regexp.pattern, text)
            raise self.failureException(msg)

    def _assertIn(self, member, container, msg=None):
        """Just like self.assertTrue(a in b), but with a nicer default message."""
        if member not in container:
            standardMsg = '%s not found in %s' % (safe_repr(member),
                                                  safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))



class MockResponse():
    def __init__(self, status, data='{}'):
        self.status_code = status
        self.content = data
        self.headers = {}

    def json(self):
        """Returns the json-encoded content of a response, if any."""
        return json.loads(self.content)


class UploadCareTest(ModernTestCase):

    @patch('requests.request', autospec=True)
    def test_raises(self, request):
        ucare = UploadCare('pub', 'secret')

        request.return_value = MockResponse(404, '{}')
        with self._assertRaises(UploadCareException):
            ucare.make_request('GET', '/files/')

        request.return_value = MockResponse(200, 'meh')
        with self._assertRaises(APIError) as cm:
            ucare.make_request('GET', '/files/')

        self.assertEqual('API error: No JSON object could be decoded',
                         cm.exception.message)

    @patch('requests.request', autospec=True)
    def test_request_headers(self, request):

        request.return_value = MockResponse(200, '[]')

        ucare = UploadCare('pub', 'secret')
        ucare.make_request('GET', '/files/')
        headers = request.call_args[1]['headers']
        self._assertIn('Accept', headers)
        self._assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'],
                         'application/vnd.uploadcare-v0.2+json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.14')

        ucare = UploadCare('pub', 'secret', api_version='0.1')
        ucare.make_request('GET', '/files/')
        headers = request.call_args[1]['headers']
        self._assertIn('Accept', headers)
        self._assertIn('User-Agent', headers)
        self.assertEqual(headers['Accept'], 'application/vnd.uploadcare-v0.1+json')
        self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.14')

    def test_uri_builders(self):
        ucare = UploadCare('pub', 'secret')
        path = ucare._build_api_path('/files/?asd=1')
        uri = ucare._build_api_uri(path)
        self.assertEqual(path, '/files/?asd=1')
        self.assertEqual(uri, 'https://api.uploadcare.com/files/?asd=1')

        ucare = UploadCare('pub', 'secret', api_base='http://example.com/api')
        path = ucare._build_api_path('/files/?asd=1')
        uri = ucare._build_api_uri(path)
        self.assertEqual(path, '/api/files/?asd=1')
        self.assertEqual(uri, 'http://example.com/api/files/?asd=1')


class FileTest(ModernTestCase):
    @patch('requests.head', autospec=True)
    @patch('requests.request', autospec=True)
    def test_store_timeout(self, request, head):
        ucare = UploadCare('pub', 'secret')
        api_response = MockResponse(200, '{"on_s3": false, "last_keep_claim": null}')
        request.return_value = api_response
        cdn_response = MockResponse(200)
        head.return_value = cdn_response

        f = File('uuid', ucare)
        with self._assertRaises(Exception) as cm:
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

        f = File('uuid', ucare)
        with self._assertRaises(Exception) as cm:
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
        request.return_value = MockResponse(200,
            '{"original_file_url": "meh"}')

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
        with self._assertRaises(ValueError):
            f.cropped_40
        with self._assertRaises(ValueError):
            f.resized_
        with self._assertRaises(ValueError):
            f.resized_1x1x1

    @patch('requests.head', autospec=True)
    @patch('requests.request', autospec=True)
    def test_ensure_on_cdn_raises(self, request, head):
        ucare = UploadCare('pub', 'secret')
        uuid = '6c5e9526-b0fe-4739-8975-72e8d5ee6342'
        f = ucare.file(uuid)
        api_response = MockResponse(200, '{"on_s3": true, "last_keep_claim": true}')
        request.return_value = api_response
        cdn_response = MockResponse(404)
        head.return_value = cdn_response
        with self._assertRaises(Exception) as cm:
            f.store(wait=True, timeout=0.1)
        self.assertEqual('timed out waiting for file appear on cdn', cm.exception.message)

class TestFormFields(ModernTestCase):

    @override_settings(UPLOADCARE={'pub_key': 'asdf', 'secret': 'qwer'})
    def test_default_form_field(self):

        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField()

        f = SomeForm()
        self._assertRegexpMatches(str(f.media),
            'https://ucarecdn\.com/widget/[\d\.]+/uploadcare/uploadcare-[\d\.]+\.min\.js')
        self._assertIn('role="uploadcare-uploader"', str(f['ff']))
        self._assertIn('data-public-key="asdf"', str(f['ff']))
        self._assertIn('type="hidden"', str(f['ff']))

    @override_settings(UPLOADCARE={'pub_key': 'asdf', 'secret': 'qwer'})
    def test_form_field_custom_attrs(self):

        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField(
                widget=uc_forms.FileWidget(attrs={'role': 'role'}))

        f = SomeForm()
        self._assertRegexpMatches(str(f.media),
            'https://ucarecdn\.com/widget/[\d\.]+/uploadcare/uploadcare-[\d\.]+\.min\.js')
        self._assertIn('role="role"', str(f['ff']))
        self._assertIn('data-public-key="asdf"', str(f['ff']))
        self._assertIn('type="hidden"', str(f['ff']))
