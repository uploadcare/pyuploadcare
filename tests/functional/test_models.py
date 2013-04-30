# coding: utf-8
from __future__ import unicode_literals
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from django.core.exceptions import ValidationError
from django.db import models

from pyuploadcare.dj.models import ImageField, FileField, FileGroupField
from pyuploadcare.api_resources import File, FileGroup


class CropToolRegexTest(unittest.TestCase):

    def test_crop_tool_is_none(self):
        ImageField()

    def test_crop_tool_is_empty_str(self):
        ImageField("")

    def test_crop_tool_is_empty_unicode(self):
        ImageField("")

    def test_crop_tool_is_disabled(self):
        ImageField("disabled")

    def test_crop_tool_is_2colon3(self):
        ImageField("2:3")

    def test_crop_tool_is_200x300(self):
        ImageField("200x300")

    def test_crop_tool_is_200x300_upscale(self):
        ImageField("200x300 upscale")

    def test_validation_error_when_crop_tool_is_200colon300_upscale(self):
        self.assertRaises(ValidationError, ImageField, "200:300 upscale")

    def test_validation_error_when_crop_tool_is_int(self):
        self.assertRaises(ValidationError, ImageField, 123)


class FileFieldTest(unittest.TestCase):

    def test_empty_str_is_allowed(self):
        class Employee(models.Model):
            cv = FileField(blank=True)
        emp = Employee()
        self.assertEqual(emp.cv, '')

    def test_null_is_allowed(self):
        class Employee(models.Model):
            cv = FileField(null=True)
        emp = Employee(cv=None)
        self.assertEqual(emp.cv, None)

    def test_validation_error_if_value_is_int(self):
        class Employee(models.Model):
            cv = FileField()
        with self.assertRaises(ValidationError):
            Employee(cv=123)

    def test_validation_error_if_uuid_is_invalid_str(self):
        class Employee(models.Model):
            cv = FileField()
        with self.assertRaises(ValidationError):
            Employee(cv='123')

    def test_file_instance_if_uuid_is_valid(self):
        class Employee(models.Model):
            cv = FileField()
        emp = Employee(cv='3addab78-6368-4c55-ac08-22412b6a2a4c')
        self.assertIsInstance(emp.cv, File)


class FileGroupFieldTest(unittest.TestCase):

    def test_empty_str_is_allowed(self):
        class Book(models.Model):
            pages = FileGroupField(blank=True)
        book = Book()
        self.assertEqual(book.pages, '')

    def test_null_is_allowed(self):
        class Book(models.Model):
            pages = FileGroupField(null=True)
        book = Book(pages=None)
        self.assertEqual(book.pages, None)

    def test_validation_error_if_value_is_int(self):
        class Book(models.Model):
            pages = FileGroupField()
        with self.assertRaises(ValidationError):
            Book(pages=123)

    def test_validation_error_if_group_id_is_invalid_str(self):
        class Book(models.Model):
            pages = FileGroupField()
        with self.assertRaises(ValidationError):
            Book(pages='123')

    def test_file_group_instance_if_group_id_is_valid(self):
        class Book(models.Model):
            pages = FileGroupField()
        book = Book(pages='0513dda0-582f-447d-846f-096e5df9e2bb~2')
        self.assertIsInstance(book.pages, FileGroup)
