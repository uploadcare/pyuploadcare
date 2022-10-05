# coding: utf-8

import unittest

from django.core.exceptions import ValidationError
from django.db import models

from pyuploadcare import File, FileGroup
from pyuploadcare.dj.models import FileField, FileGroupField, ImageField


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
    def _construct_Employee_class_with_variations(self, label, cv_field):
        class Meta:
            app_label = "tests"

        bases = (models.Model,)
        attributes = {"Meta": Meta, "cv": cv_field, "__module__": __name__}
        return type(f"Employee_{label}", bases, attributes)

    def test_empty_str_is_allowed(self):
        Employee = self._construct_Employee_class_with_variations(
            "blank", FileField(blank=True)
        )
        emp = Employee()
        self.assertEqual(emp.cv, "")

    def test_null_is_allowed(self):
        Employee = self._construct_Employee_class_with_variations(
            "null", FileField(null=True)
        )

        emp = Employee(cv=None)
        self.assertEqual(emp.cv, None)

    def test_validation_error_if_value_is_int(self):
        Employee = self._construct_Employee_class_with_variations(
            "int", FileField()
        )

        with self.assertRaises(ValidationError):
            Employee(cv=123)

    def test_validation_error_if_uuid_is_invalid_str(self):
        Employee = self._construct_Employee_class_with_variations(
            "invalid_str", FileField()
        )

        with self.assertRaises(ValidationError):
            Employee(cv="123")

    def test_file_instance_if_uuid_is_valid(self):
        Employee = self._construct_Employee_class_with_variations(
            "valid_uuid_str", FileField()
        )

        emp = Employee(cv="3addab78-6368-4c55-ac08-22412b6a2a4c")
        self.assertIsInstance(emp.cv, File)


class FileGroupFieldTest(unittest.TestCase):
    def _construct_Book_class_with_variations(self, label, pages_field):
        class Meta:
            app_label = "tests"

        bases = (models.Model,)
        attributes = {
            "Meta": Meta,
            "pages": pages_field,
            "__module__": __name__,
        }
        return type(f"Book_{label}", bases, attributes)

    def test_empty_str_is_allowed(self):
        Book = self._construct_Book_class_with_variations(
            "empty", FileGroupField(blank=True)
        )

        book = Book()
        self.assertEqual(book.pages, "")

    def test_null_is_allowed(self):
        Book = self._construct_Book_class_with_variations(
            "null", FileGroupField(null=True)
        )

        book = Book(pages=None)
        self.assertEqual(book.pages, None)

    def test_validation_error_if_value_is_int(self):
        Book = self._construct_Book_class_with_variations(
            "int", FileGroupField()
        )

        with self.assertRaises(ValidationError):
            Book(pages=123)

    def test_validation_error_if_group_id_is_invalid_str(self):
        Book = self._construct_Book_class_with_variations(
            "invalid_str", FileGroupField()
        )

        with self.assertRaises(ValidationError):
            Book(pages="123")

    def test_file_group_instance_if_group_id_is_valid(self):
        Book = self._construct_Book_class_with_variations(
            "valid_str", FileGroupField()
        )

        book = Book(pages="0513dda0-582f-447d-846f-096e5df9e2bb~2")
        self.assertIsInstance(book.pages, FileGroup)
