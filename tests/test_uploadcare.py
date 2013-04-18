# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pyuploadcare.file import File, FileGroup
from pyuploadcare.exceptions import InvalidRequestError


class FileRegexTest(unittest.TestCase):

    def test_value_error_when_uuid_is_bad(self):
        file_serialized = 'blah'
        self.assertRaises(InvalidRequestError, File, file_serialized)

    def test_only_uuid(self):
        file_serialized = '3addab78-6368-4c55-ac08-22412b6a2a4c'
        expected_cdn_url = 'https://ucarecdn.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_arbitrary_domain(self):
        file_serialized = 'http://example.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'
        expected_cdn_url = 'https://ucarecdn.com/3addab78-6368-4c55-ac08-22412b6a2a4c/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_crop_effect(self):
        file_serialized = 'cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'
        expected_cdn_url = 'https://ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)

    def test_uuid_and_crop_effect_and_arbitrary_domain(self):
        file_serialized = 'https://ucarecdn.com/cde35b21-c5e1-4ed4-b2fc-d4ef4b0538b0/-/crop/296x445/251,81/'
        expected_cdn_url = file_serialized

        file_ = File(file_serialized)
        self.assertEqual(file_.cdn_url, expected_cdn_url)


class FileGroupRegexTest(unittest.TestCase):

    def test_value_error_when_uuid_is_bad(self):
        group_id = 'blah'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_value_error_when_group_id_has_not_files_qty(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_value_error_when_group_id_has_chars_instead_of_files_qty(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~blah'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_value_error_when_group_id_has_zero_files(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~0'
        self.assertRaises(InvalidRequestError, FileGroup, group_id)

    def test_valid_group_id(self):
        group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~12'
        expected_cdn_url = 'https://ucarecdn.com/d5f45851-3a58-41a4-b76c-356e22837a2f~12/'

        group = FileGroup(group_id)
        self.assertEqual(group.cdn_url, expected_cdn_url)
        self.assertEqual(len(group), 12)

    def test_extracting_group_id_from_url(self):
        cdn_url = 'https://ucarecdn.com/d5f45851-3a58-41a4-b76c-356e22837a2f~12/'
        expected_group_id = 'd5f45851-3a58-41a4-b76c-356e22837a2f~12'

        group = FileGroup(cdn_url)
        self.assertEqual(group.id, expected_group_id)
        self.assertEqual(len(group), 12)
