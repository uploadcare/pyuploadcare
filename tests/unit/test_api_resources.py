# coding: utf-8
from __future__ import unicode_literals
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pyuploadcare.api_resources import FileList


class FileListIteratorInitTest(unittest.TestCase):
    """Tests determining of API page based on given offset."""

    def test_page_2_position_0_when_total_11_per_page_3_offset_4(self):
        """| 1 2 3 | 4 5 6 | 7 8 9 | 10 11 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=4)

        self.assertEqual(gen._page, 2)
        self.assertEqual(gen._position_in_page, 0)

    def test_page_2_position_1_when_total_11_per_page_3_offset_5(self):
        """| 1 2 3 | 4 5 6 | 7 8 9 | 10 11 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=5)

        self.assertEqual(gen._page, 2)
        self.assertEqual(gen._position_in_page, 1)

    def test_page_2_position_2_when_total_11_per_page_3_offset_6(self):
        """| 1 2 3 | 4 5 6 | 7 8 9 | 10 11 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=6)

        self.assertEqual(gen._page, 2)
        self.assertEqual(gen._position_in_page, 2)

    def test_page_1_position_4_when_total_11_per_page_11_offset_5(self):
        """| 1 2 3 4 5 6 7 8 9 10 11 |"""
        FileList.FileListIterator._count_per_request = 11
        gen = FileList.FileListIterator(offset=5)

        self.assertEqual(gen._page, 1)
        self.assertEqual(gen._position_in_page, 4)

    def test_page_1_position_11_when_total_11_per_page_13_offset_12(self):
        """| 1 2 3 4 5 6 7 8 9 10 11 _ _ |"""
        FileList.FileListIterator._count_per_request = 13
        gen = FileList.FileListIterator(offset=12)

        self.assertEqual(gen._page, 1)
        self.assertEqual(gen._position_in_page, 11)
