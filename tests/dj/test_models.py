# coding: utf-8
from __future__ import unicode_literals
import unittest
import os
import sys

# Add project folder to PATH for avoiding troubles in Django < 1.8
# It can't find `gallery` app
sys.path.append('test_project')
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

# Load models for avoiding 'AppRegistryNotReady: Models aren't loaded yet.'
# in Django 1.7.10
import django
if hasattr(django, 'setup'):
    django.setup()

import six

if six.PY3:
    from unittest.mock import patch
else:
    from mock import patch

from django.core.exceptions import ValidationError
from django.db import models

from pyuploadcare.dj.models import ImageField, FileField, FileGroupField
from pyuploadcare.api_resources import File, FileGroup
from pyuploadcare.exceptions import InvalidRequestError


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

    def test_crop_tool_is_200x300_minimum(self):
        ImageField("200x300 minimum")

    def test_validation_error_when_crop_tool_is_200x300_maximum(self):
        self.assertRaises(ValidationError, ImageField, "200x300 maximum")

    def test_validation_error_when_crop_tool_is_200colon300_upscale(self):
        self.assertRaises(ValidationError, ImageField, "200:300 upscale")

    def test_validation_error_when_crop_tool_is_int(self):
        self.assertRaises(ValidationError, ImageField, 123)


class FileFieldTest(unittest.TestCase):

    def test_empty_str_is_allowed(self):
        class Employee(models.Model):
            class Meta:
                app_label = 'tests'
            cv = FileField(blank=True)
        emp = Employee()
        self.assertEqual(emp.cv, '')

    def test_null_is_allowed(self):
        class Employee(models.Model):
            class Meta:
                app_label = 'tests'
            cv = FileField(null=True)
        emp = Employee(cv=None)
        self.assertEqual(emp.cv, None)

    def test_validation_error_if_value_is_int(self):
        class Employee(models.Model):
            class Meta:
                app_label = 'tests'
            cv = FileField()
        with self.assertRaises(ValidationError):
            Employee(cv=123)

    def test_validation_error_if_uuid_is_invalid_str(self):
        class Employee(models.Model):
            class Meta:
                app_label = 'tests'
            cv = FileField()
        with self.assertRaises(ValidationError):
            Employee(cv='123')

    def test_file_instance_if_uuid_is_valid(self):
        class Employee(models.Model):
            class Meta:
                app_label = 'tests'
            cv = FileField()
        emp = Employee(cv='3addab78-6368-4c55-ac08-22412b6a2a4c')
        self.assertIsInstance(emp.cv, File)

    @patch('pyuploadcare.api_resources.rest_request', autospec=True)
    def test_not_found_file_uuid(self, request):
        request.side_effect = InvalidRequestError(404)

        # Just for calling `value.info` inside `Field.clean` method.
        faked_size_validator = lambda value: value.info()['size']

        class Employee(models.Model):
            class Meta:
                app_label = 'tests'
            cv = FileField(validators=[faked_size_validator])

        emp = Employee(cv='3addab78-6368-4c55-ac08-22412b6a2a4c')

        with self.assertRaises(ValidationError):
            emp._meta.get_field('cv').clean(emp.cv, emp)


class FileGroupFieldTest(unittest.TestCase):

    def test_empty_str_is_allowed(self):
        class Book(models.Model):
            class Meta:
                app_label = 'tests'
            pages = FileGroupField(blank=True)
        book = Book()
        self.assertEqual(book.pages, '')

    def test_null_is_allowed(self):
        class Book(models.Model):
            class Meta:
                app_label = 'tests'
            pages = FileGroupField(null=True)
        book = Book(pages=None)
        self.assertEqual(book.pages, None)

    def test_validation_error_if_value_is_int(self):
        class Book(models.Model):
            class Meta:
                app_label = 'tests'
            pages = FileGroupField()
        with self.assertRaises(ValidationError):
            Book(pages=123)

    def test_validation_error_if_group_id_is_invalid_str(self):
        class Book(models.Model):
            class Meta:
                app_label = 'tests'
            pages = FileGroupField()
        with self.assertRaises(ValidationError):
            Book(pages='123')

    def test_file_group_instance_if_group_id_is_valid(self):
        class Book(models.Model):
            class Meta:
                app_label = 'tests'
            pages = FileGroupField()
        book = Book(pages='0513dda0-582f-447d-846f-096e5df9e2bb~2')
        self.assertIsInstance(book.pages, FileGroup)
