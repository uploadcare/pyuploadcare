# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pyuploadcare.utils import urljoin


class UrljoinTest(unittest.TestCase):

    def test_base_url_path_value_is_empty(self):
        url = urljoin('http://example.com', '/files/?asd=1')
        self.assertEqual(url, 'http://example.com/files/?asd=1')

    def test_base_url_path_value_is_slash(self):
        url = urljoin('http://example.com/', '/files/?asd=1')
        self.assertEqual(url, 'http://example.com/files/?asd=1')

    def test_base_url_path_value_is_api(self):
        url = urljoin('http://example.com/api', '/files/?asd=1')
        self.assertEqual(url, 'http://example.com/api/files/?asd=1')

    def test_base_url_path_value_has_query(self):
        url = urljoin('http://example.com/api?fizz=buzz', '/files/?asd=1')
        self.assertEqual(url, 'http://example.com/api/files/?fizz=buzz&asd=1')
