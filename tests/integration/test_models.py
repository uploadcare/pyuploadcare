# coding: utf-8
from __future__ import unicode_literals

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


class ModelFormIntegrationTest(unittest.TestCase):

    def test_validation_error_if_uuid_is_invalid(self):
        class Employee(models.Model):
            cv = uc_models.FileField()
            class Meta:
                app_label = 'tests.integration.test_models.test_validation_error_if_uuid_is_invalid.Employee'
        class EmployeeForm(forms.ModelForm):
            class Meta:
                model = Employee
                fields = ['cv']
        form = EmployeeForm(data={'cv': '99999999-9999-9999-9999-999999999999'})
        form.full_clean()
        self.assertIsNotNone(form.errors)
