# coding: utf-8
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

from django.test.utils import override_settings
from django import forms

from pyuploadcare.dj import forms as uc_forms


class TestFormFields(unittest.TestCase):

    @override_settings(UPLOADCARE={'pub_key': 'asdf', 'secret': 'qwer'})
    def test_default_form_field(self):

        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField()

        f = SomeForm()
        self.assertRegexpMatches(
            str(f.media),
            'https://ucarecdn\.com/widget/[\d\.]+/uploadcare/uploadcare-[\d\.]+\.min\.js'
        )
        self.assertIn('role="uploadcare-uploader"', str(f['ff']))
        self.assertIn('data-public-key="asdf"', str(f['ff']))
        self.assertIn('type="hidden"', str(f['ff']))

    @override_settings(UPLOADCARE={'pub_key': 'asdf', 'secret': 'qwer'})
    def test_form_field_custom_attrs(self):

        class SomeForm(forms.Form):
            cf = forms.CharField()
            ff = uc_forms.FileField(
                widget=uc_forms.FileWidget(attrs={'role': 'role'}))

        f = SomeForm()
        self.assertRegexpMatches(
            str(f.media),
            'https://ucarecdn\.com/widget/[\d\.]+/uploadcare/uploadcare-[\d\.]+\.min\.js'
        )
        self.assertIn('role="role"', str(f['ff']))
        self.assertIn('data-public-key="asdf"', str(f['ff']))
        self.assertIn('type="hidden"', str(f['ff']))
