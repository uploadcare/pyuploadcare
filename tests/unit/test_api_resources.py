# coding: utf-8
from __future__ import unicode_literals
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pyuploadcare.api_resources import FileList


class FileListIteratorInitTest(unittest.TestCase):
    """Tests determining of API page based on given offset."""

    def test_page_1_position_0_when_total_11_per_page_3_offset_0(self):
        """| 0 1 2 | 3 4 5 | 6 7 8 | 9 10 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=0)

        self.assertEqual(gen._page, 1)
        self.assertEqual(gen._position_in_page, 0)

    def test_page_1_position_1_when_total_11_per_page_3_offset_1(self):
        """| 0 1 2 | 3 4 5 | 6 7 8 | 9 10 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=1)

        self.assertEqual(gen._page, 1)
        self.assertEqual(gen._position_in_page, 1)

    def test_page_1_position_2_when_total_11_per_page_3_offset_2(self):
        """| 0 1 2 | 3 4 5 | 6 7 8 | 9 10 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=2)

        self.assertEqual(gen._page, 1)
        self.assertEqual(gen._position_in_page, 2)

    def test_page_2_position_0_when_total_11_per_page_3_offset_3(self):
        """| 0 1 2 | 3 4 5 | 6 7 8 | 9 10 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=3)

        self.assertEqual(gen._page, 2)
        self.assertEqual(gen._position_in_page, 0)

    def test_page_2_position_1_when_total_11_per_page_3_offset_4(self):
        """| 0 1 2 | 3 4 5 | 6 7 8 | 9 10 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=4)

        self.assertEqual(gen._page, 2)
        self.assertEqual(gen._position_in_page, 1)

    def test_page_2_position_2_when_total_11_per_page_3_offset_5(self):
        """| 0 1 2 | 3 4 5 | 6 7 8 | 9 10 _ |"""
        FileList.FileListIterator._count_per_request = 3
        gen = FileList.FileListIterator(offset=5)

        self.assertEqual(gen._page, 2)
        self.assertEqual(gen._position_in_page, 2)

    def test_page_1_position_4_when_total_11_per_page_11_offset_4(self):
        """| 0 1 2 3 4 5 6 7 8 9 10 |"""
        FileList.FileListIterator._count_per_request = 11
        gen = FileList.FileListIterator(offset=4)

        self.assertEqual(gen._page, 1)
        self.assertEqual(gen._position_in_page, 4)

    def test_page_1_position_11_when_total_11_per_page_13_offset_11(self):
        """| 0 1 2 3 4 5 6 7 8 9 10 _ _ |"""
        FileList.FileListIterator._count_per_request = 13
        gen = FileList.FileListIterator(offset=11)

        self.assertEqual(gen._page, 1)
        self.assertEqual(gen._position_in_page, 11)
