# coding: utf-8
from __future__ import unicode_literals
from tests.integration.utils import upload_tmp_txt_file

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

import django
django.setup()

from django import forms
from django.db import models
from pyuploadcare.dj import models as uc_models


class Employee(models.Model):
    cv = uc_models.FileField()
    class Meta:
        app_label = 'tests.integration.test_models.Employee'


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['cv']


class ModelFormIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_ = upload_tmp_txt_file(content='hello')

    def test_no_validation_error_if_uuid_is_valid(self):
        form = EmployeeForm(data={'cv': ModelFormIntegrationTest.file_.uuid})
        form.full_clean()
        self.assertEquals(form.errors, {})

    def test_validation_error_if_uuid_is_invalid(self):
        form = EmployeeForm(data={'cv': '99999999-9999-9999-9999-999999999999'})
        form.full_clean()
        self.assertIsNotNone(form.errors)
